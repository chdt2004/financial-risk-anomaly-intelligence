"""Meaningful regression checks: leakage, corruption, reconciliations and frozen policies."""
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from run_project import ROOT, FEATURES, engineer_features, validate_sources


def main():
    names=['TRANSACTIONS','ACCOUNTS','MERCHANTS','TRANSACTION_TYPES','DATES','SCENARIO_LABELS','REVIEWS']
    frames={n:pd.read_csv(ROOT/'data/raw'/f'{n}.csv') for n in names}
    validate_sources(frames)
    passed=[]
    def rejected(label,mutate):
        copy={n:f.copy(deep=True) for n,f in frames.items()}
        mutate(copy)
        try:validate_sources(copy)
        except ValueError:passed.append(label)
        else:raise AssertionError(f'Corruption escaped validation: {label}')
    rejected('duplicate transaction detected',lambda d:d.__setitem__('TRANSACTIONS',pd.concat([d['TRANSACTIONS'],d['TRANSACTIONS'].iloc[[0]]],ignore_index=True)))
    def set_cell(d,table,column,value):
        d[table].loc[0,column]=value
    rejected('orphan account detected',lambda d:set_cell(d,'TRANSACTIONS','ACCOUNT_ID','UNKNOWN'))
    rejected('invalid timestamp detected',lambda d:set_cell(d,'TRANSACTIONS','TX_TIMESTAMP','not-a-date'))
    rejected('negative amount detected',lambda d:set_cell(d,'TRANSACTIONS','AMOUNT_GBP',-1))
    rejected('missing merchant category detected',lambda d:set_cell(d,'MERCHANTS','MERCHANT_CATEGORY',None))
    t=frames['TRANSACTIONS']
    f=engineer_features(t)
    # Appending future events must not change earlier features.
    prefix=t[pd.to_datetime(t.TX_TIMESTAMP)<'2025-05-01']
    pre=engineer_features(prefix)
    compare=f.set_index('TRANSACTION_ID').loc[pre.TRANSACTION_ID,FEATURES].to_numpy()
    np.testing.assert_allclose(compare,pre[FEATURES].to_numpy(),rtol=0,atol=0)
    passed.append('future events do not alter prior features')
    # Own amount must not change own prior mean/count/gap.
    pos=1000
    changed=t.copy();changed.loc[pos,'AMOUNT_GBP']*=100
    own=engineer_features(changed).set_index('TRANSACTION_ID').loc[t.iloc[pos].TRANSACTION_ID]
    old=f.set_index('TRANSACTION_ID').loc[t.iloc[pos].TRANSACTION_ID]
    for col in ['PRIOR_MEAN_GBP','PRIOR_COUNT_1H','GAP_SECONDS']:assert own[col]==old[col],col
    passed.append('current amount excluded from own historical features')
    # Concrete event-time window example, including hour boundary and other account.
    sample=pd.DataFrame({'TRANSACTION_ID':['X1','Y1','X2','X3','X4'],'ACCOUNT_ID':['X','Y','X','X','X'],'TX_TIMESTAMP':['2025-01-01 00:00:00','2025-01-01 00:05:00','2025-01-01 00:10:00','2025-01-01 01:00:00','2025-01-01 01:00:01'],'AMOUNT_GBP':[10.,999.,30.,20.,100.]})
    g=engineer_features(sample).set_index('TRANSACTION_ID')
    assert g.loc['X3','PRIOR_COUNT_1H']==2
    assert g.loc['X4','PRIOR_COUNT_1H']==2
    assert g.loc['X3','PRIOR_MEAN_GBP']==20
    assert g.loc['X2','GAP_SECONDS']==600
    passed.append('strict past per-account features and hour boundary verified')
    risk=pd.read_csv(ROOT/'data/processed/TRANSACTION_RISK.csv')
    assert not set(['SCENARIO_LABEL','SCENARIO_TYPE','REVIEW_STATUS']).intersection(FEATURES)
    assert 'SCENARIO_LABEL' not in risk and 'SCENARIO_TYPE' not in risk
    passed.append('labels excluded from model and deployed risk file')
    meta=json.loads((ROOT/'outputs/model_metadata.json').read_text())
    validation=risk[risk.SPLIT=='VALIDATION']
    for q in [90,95,98,99]:assert abs(validation.ANOMALY_SCORE.quantile(q/100)-meta['thresholds'][f'Q{q}'])<1e-9
    assert (risk.ALERT_FLAG==(risk.ANOMALY_SCORE>=round(meta['thresholds']['Q98'],10)).astype(int)).all()
    passed.append('thresholds reproduced from validation and frozen flags verified')
    metrics=pd.read_csv(ROOT/'data/processed/THRESHOLD_METRICS.csv')
    for _,group in metrics.groupby('SPLIT'):
        group=group.sort_values('THRESHOLD')
        assert group.ALERT_COUNT.diff().dropna().le(0).all()
        assert group.TP.diff().dropna().le(0).all()
        assert group.FN.diff().dropna().ge(0).all()
        assert (group.TP+group.FP+group.FN+group.TN==group.TRANSACTION_COUNT).all()
    passed.append('threshold monotonicity and confusion matrix identities')
    with sqlite3.connect(ROOT/'outputs/risk_warehouse.sqlite') as db:
        # Add another review event; preaggregation must preserve transaction count/value.
        before=pd.read_sql_query('SELECT COUNT(*) N,SUM(AMOUNT_GBP) V FROM V_RISK_DETAIL',db).iloc[0]
        db.execute("INSERT INTO REVIEWS SELECT 'EXTRA_TEST_REVIEW',TRANSACTION_ID,REVIEW_TIMESTAMP,REVIEW_STATUS FROM REVIEWS LIMIT 1")
        after=pd.read_sql_query('SELECT COUNT(*) N,SUM(AMOUNT_GBP) V FROM V_RISK_DETAIL',db).iloc[0]
        np.testing.assert_allclose(before,after)
        db.rollback()
    passed.append('multiple review events do not duplicate transaction amounts')
    report={'passed':len(passed),'tests':passed}
    (ROOT/'outputs/regression_tests.json').write_text(json.dumps(report,indent=2))
    print(f'VERIFIED: {len(passed)} regression checks passed.')


if __name__=='__main__':main()
