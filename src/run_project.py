"""Reproducible educational batch anomaly analytics. Run from any directory."""
from pathlib import Path
from collections import deque
import json
import sqlite3
import platform
import sys
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, precision_recall_curve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW, PROCESSED, OUT = [ROOT / p for p in ('data/raw', 'data/processed', 'outputs')]
FEATURES = ['LOG_AMOUNT', 'AMOUNT_RATIO', 'PRIOR_COUNT_1H', 'LOG_GAP_SECONDS', 'NIGHT_FLAG']


def generate_data():
    """Independent seeded scenarios; all amounts positive GBP purchase payments."""
    rng = np.random.default_rng(42)
    accounts = pd.DataFrame({'ACCOUNT_ID': [f'A{i:04}' for i in range(1, 201)],
                             'ACCOUNT_TYPE': ['Personal' if i % 4 else 'Business' for i in range(200)],
                             'OPEN_DATE': [(pd.Timestamp('2019-01-01') + pd.Timedelta(days=int(x))).strftime('%Y-%m-%d') for x in rng.integers(0, 1800, 200)]})
    merchants = pd.DataFrame({'MERCHANT_ID': [f'M{i:03}' for i in range(1, 41)],
                              'MERCHANT_CATEGORY': np.tile(['Groceries', 'Travel', 'Electronics', 'Dining', 'Services'], 8),
                              'MERCHANT_REGION': np.tile(['North', 'South', 'East', 'West'], 10)})
    rows = []
    start = pd.Timestamp('2025-01-01')
    for ai, a in enumerate(accounts.ACCOUNT_ID):
        scale = rng.uniform(15, 100) * (2 if accounts.iloc[ai].ACCOUNT_TYPE == 'Business' else 1)
        # Mostly daytime ordinary payments, with legitimate tail events and night purchases.
        for _ in range(100):
            ts = start + pd.Timedelta(days=int(rng.integers(0, 180)), hours=int(rng.choice(np.arange(24), p=np.array([1]*7+[4]*15+[1]*2)/69)), minutes=int(rng.integers(0,60)), seconds=int(rng.integers(0,60)))
            rows.append([a, str(rng.choice(merchants.MERCHANT_ID)), ts, round(float(rng.lognormal(np.log(scale), .85)), 2), 0, 'Ordinary'])
        # All accounts have legitimate unusual purchases: avoid equating every outlier to a case.
        for day in [35, 95, 155]:
            ts = start + pd.Timedelta(days=day, hours=14, minutes=int(rng.integers(0,60)), seconds=ai)
            rows.append([a, str(rng.choice(merchants.MERCHANT_ID)), ts, round(scale*25, 2), 0, 'Legitimate large purchase'])
        for day in [50, 110, 170]:
            if ai % 4 == 0:
                ts = start + pd.Timedelta(days=day, hours=2, minutes=ai%60)
                rows.append([a, str(rng.choice(merchants.MERCHANT_ID)), ts, round(scale*float(rng.uniform(35,65)),2), 1, 'Injected large night payment'])
            if ai % 5 == 0:
                base = start + pd.Timedelta(days=day+1, hours=3, minutes=ai%60)
                for k in range(6):
                    rows.append([a, str(rng.choice(merchants.MERCHANT_ID)), base+pd.Timedelta(seconds=k*12), round(scale*float(rng.uniform(1,4)),2), 1, 'Injected rapid burst'])
    t = pd.DataFrame(rows, columns=['ACCOUNT_ID','MERCHANT_ID','TX_TIMESTAMP','AMOUNT_GBP','SCENARIO_LABEL','SCENARIO_TYPE']).sort_values(['TX_TIMESTAMP','ACCOUNT_ID'], kind='stable').reset_index(drop=True)
    t.insert(0, 'TRANSACTION_ID', [f'T{i:07}' for i in range(1,len(t)+1)])
    t['TX_TIMESTAMP'] = t.TX_TIMESTAMP.dt.strftime('%Y-%m-%d %H:%M:%S')
    t['TYPE_ID'], t['CURRENCY'] = 'CARD_PAYMENT', 'GBP'
    labels = t[['TRANSACTION_ID','SCENARIO_LABEL','SCENARIO_TYPE']].copy()
    tx = t.drop(columns=['SCENARIO_LABEL','SCENARIO_TYPE'])
    types = pd.DataFrame({'TYPE_ID':['CARD_PAYMENT'], 'TYPE_NAME':['Card purchase payment']})
    dates = pd.DataFrame({'TX_DATE':pd.date_range(start, periods=180).strftime('%Y-%m-%d')})
    dates['YEAR'] = 2025
    dates['MONTH_NUMBER'] = pd.to_datetime(dates.TX_DATE).dt.month
    # Review records are a small fictional administrative sample, not fraud outcomes or features.
    sample = tx.iloc[::50][['TRANSACTION_ID','TX_TIMESTAMP']].copy()
    sample['REVIEW_ID'] = [f'R{i:05}' for i in range(len(sample))]
    sample['REVIEW_TIMESTAMP'] = (pd.to_datetime(sample.TX_TIMESTAMP)+pd.Timedelta(days=3)).dt.strftime('%Y-%m-%d %H:%M:%S')
    sample['REVIEW_STATUS'] = 'DEMO_PENDING'
    sample = sample[['REVIEW_ID','TRANSACTION_ID','REVIEW_TIMESTAMP','REVIEW_STATUS']]
    for name, frame in [('ACCOUNTS',accounts),('MERCHANTS',merchants),('TRANSACTIONS',tx),('TRANSACTION_TYPES',types),('DATES',dates),('SCENARIO_LABELS',labels),('REVIEWS',sample)]:
        frame.to_csv(RAW/f'{name}.csv',index=False)


def validate_sources(frames):
    t,a,m,l,r = [frames[n] for n in ['TRANSACTIONS','ACCOUNTS','MERCHANTS','SCENARIO_LABELS','REVIEWS']]
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise ValueError(f'Validation failed: {name}')
    for name, key in [('TRANSACTIONS','TRANSACTION_ID'),('ACCOUNTS','ACCOUNT_ID'),('MERCHANTS','MERCHANT_ID'),('SCENARIO_LABELS','TRANSACTION_ID'),('TRANSACTION_TYPES','TYPE_ID'),('DATES','TX_DATE'),('REVIEWS','REVIEW_ID')]:
        f = frames[name]
        check(name+'_unique_key', f[key].notna().all() and not f[key].duplicated().any())
        check(name+'_required_values', not f.isna().any().any())
    check('positive_finite_amounts', (pd.to_numeric(t.AMOUNT_GBP,errors='coerce').gt(0) & np.isfinite(t.AMOUNT_GBP)).all())
    ts = pd.to_datetime(t.TX_TIMESTAMP,format='%Y-%m-%d %H:%M:%S',errors='coerce')
    check('valid_transaction_timestamps', ts.notna().all())
    check('account_reference', t.ACCOUNT_ID.isin(a.ACCOUNT_ID).all())
    check('merchant_reference', t.MERCHANT_ID.isin(m.MERCHANT_ID).all())
    check('type_reference', t.TYPE_ID.isin(frames['TRANSACTION_TYPES'].TYPE_ID).all())
    check('date_reference', ts.dt.strftime('%Y-%m-%d').isin(frames['DATES'].TX_DATE).all())
    check('labels_exactly_cover_transactions', set(l.TRANSACTION_ID)==set(t.TRANSACTION_ID))
    check('binary_scenario_labels', l.SCENARIO_LABEL.isin([0,1]).all())
    check('review_reference', r.TRANSACTION_ID.isin(t.TRANSACTION_ID).all())
    rt = pd.to_datetime(r.REVIEW_TIMESTAMP,errors='coerce')
    check('valid_review_timestamps', rt.notna().all())
    lookup = dict(zip(t.TRANSACTION_ID,ts))
    check('reviews_after_transactions', (rt >= r.TRANSACTION_ID.map(lookup)).all())
    opened = pd.to_datetime(a.OPEN_DATE,errors='coerce')
    check('valid_open_dates', opened.notna().all())
    check('transactions_after_account_open', (ts >= t.ACCOUNT_ID.map(dict(zip(a.ACCOUNT_ID,opened)))).all())
    check('single_gbp_currency', t.CURRENCY.eq('GBP').all())
    check('unique_account_timestamp', not t.duplicated(['ACCOUNT_ID','TX_TIMESTAMP']).any())
    return checks


def engineer_features(t):
    """Strictly prior history. Reject equal account timestamps rather than invent order."""
    t = t.copy()
    t['TS'] = pd.to_datetime(t.TX_TIMESTAMP)
    t = t.sort_values(['TS','TRANSACTION_ID']).reset_index(drop=True)
    history, prior = {}, {}
    counts, gaps, means, ns = [], [], [], []
    for row in t.itertuples():
        aid, ts = row.ACCOUNT_ID, row.TS
        window = history.setdefault(aid, deque())
        while window and (ts-window[0]).total_seconds()>3600:
            window.popleft()
        total,n,last = prior.get(aid,(0.,0,None))
        counts.append(len(window))
        gaps.append((ts-last).total_seconds() if last is not None else 86400.)
        means.append(total/n if n else 100.)
        ns.append(n)
        window.append(ts)
        prior[aid] = (total+row.AMOUNT_GBP,n+1,ts)
    t['PRIOR_COUNT_1H'], t['GAP_SECONDS'], t['PRIOR_MEAN_GBP'], t['PRIOR_HISTORY_COUNT'] = counts,gaps,means,ns
    t['LOG_AMOUNT'] = np.log1p(t.AMOUNT_GBP)
    t['AMOUNT_RATIO'] = (t.AMOUNT_GBP/t.PRIOR_MEAN_GBP).clip(upper=100)
    t['LOG_GAP_SECONDS'] = np.log1p(t.GAP_SECONDS.clip(upper=604800))
    t['NIGHT_FLAG'] = t.TS.dt.hour.lt(6).astype(int)
    t['TX_DATE'] = t.TS.dt.strftime('%Y-%m-%d')
    t['SPLIT'] = np.select([t.TS.lt('2025-04-01'),t.TS.lt('2025-05-01')],['TRAIN','VALIDATION'],default='TEST')
    return t.drop(columns='TS')


def counts_at(y,score,threshold):
    alert = score>=threshold
    tp,fp,fn,tn = [int(x) for x in [(alert & (y==1)).sum(),(alert & (y==0)).sum(),(~alert & (y==1)).sum(),(~alert & (y==0)).sum()]]
    return {'TRANSACTION_COUNT':len(y),'ALERT_COUNT':int(alert.sum()),'ALERT_VALUE_GBP':0.,'TP':tp,'FP':fp,'FN':fn,'TN':tn,'PRECISION':tp/(tp+fp) if tp+fp else None,'RECALL':tp/(tp+fn) if tp+fn else None,'ALERT_RATE':float(alert.mean())}


def main(regenerate=False):
    for p in [RAW,PROCESSED,OUT]: p.mkdir(parents=True,exist_ok=True)
    if regenerate or not (RAW/'TRANSACTIONS.csv').exists(): generate_data()
    names = ['TRANSACTIONS','ACCOUNTS','MERCHANTS','TRANSACTION_TYPES','DATES','SCENARIO_LABELS','REVIEWS']
    frames = {n:pd.read_csv(RAW/f'{n}.csv') for n in names}
    checks = validate_sources(frames)
    f = engineer_features(frames['TRANSACTIONS'])
    model = IsolationForest(n_estimators=200,max_samples=256,contamination='auto',random_state=42,n_jobs=1)
    model.fit(f.loc[f.SPLIT.eq('TRAIN'),FEATURES])
    # Negate native score_samples: higher score = more anomalous. Not probability.
    f['ANOMALY_SCORE'] = -model.score_samples(f[FEATURES])
    val = f[f.SPLIT.eq('VALIDATION')]
    thresholds = {f'Q{q}':float(val.ANOMALY_SCORE.quantile(q/100)) for q in [90,95,98,99]}
    threshold = thresholds['Q98']  # Fixed capacity policy, selected without labels.
    f['ALERT_FLAG'] = (f.ANOMALY_SCORE>=threshold).astype(int)
    f['TX_COUNT'] = 1
    f['ALERT_AMOUNT_GBP'] = f.AMOUNT_GBP*f.ALERT_FLAG
    f['RISK_BAND'] = np.where(f.ALERT_FLAG.eq(1),'High anomaly',np.where(f.ANOMALY_SCORE>=thresholds['Q95'],'Elevated anomaly','Baseline'))
    f['SCORE_BIN'] = pd.cut(f.ANOMALY_SCORE,[-np.inf,.4,.45,.5,.55,.6,.65,np.inf],labels=['01 Below .40','02 .40-.45','03 .45-.50','04 .50-.55','05 .55-.60','06 .60-.65','07 .65 and above'],right=False).astype(str)
    f['INDICATOR_AMOUNT'] = (f.AMOUNT_RATIO>=5).astype(int)
    f['INDICATOR_VELOCITY'] = (f.PRIOR_COUNT_1H>=3).astype(int)
    f['INDICATOR_SHORT_GAP'] = (f.GAP_SECONDS<60).astype(int)
    f['INDICATOR_NIGHT'] = f.NIGHT_FLAG
    f['REVIEW_HINT'] = [('; '.join([text for flag,text in [(r.INDICATOR_AMOUNT,'Amount >=5x prior mean'),(r.INDICATOR_VELOCITY,'3+ prior payments in hour'),(r.INDICATOR_SHORT_GAP,'Gap under 60 seconds'),(r.INDICATOR_NIGHT,'Payment before 06:00')] if flag]) or 'Unusual feature combination; inspect context') for r in f.itertuples()]
    f.to_csv(PROCESSED/'TRANSACTION_RISK.csv',index=False,float_format='%.10f')
    # Labels joined ONLY after modelling. Never deployed to transaction risk model.
    e = f.merge(frames['SCENARIO_LABELS'],on='TRANSACTION_ID',validate='one_to_one')
    table=[]
    for split in ['VALIDATION','TEST']:
        part=e[e.SPLIT.eq(split)]
        for policy,cut in thresholds.items():
            row={'SPLIT':split,'POLICY_ID':policy,'THRESHOLD':cut,**counts_at(part.SCENARIO_LABEL,part.ANOMALY_SCORE,cut)}
            row['ALERT_VALUE_GBP']=float(part.loc[part.ANOMALY_SCORE>=cut,'AMOUNT_GBP'].sum())
            table.append(row)
    metrics=pd.DataFrame(table)
    metrics.to_csv(PROCESSED/'THRESHOLD_METRICS.csv',index=False,float_format='%.10f')
    test=e[e.SPLIT.eq('TEST')]
    p,r,_=precision_recall_curve(test.SCENARIO_LABEL,test.ANOMALY_SCORE)
    ap=average_precision_score(test.SCENARIO_LABEL,test.ANOMALY_SCORE)
    pd.DataFrame({'PRECISION':p,'RECALL':r}).to_csv(OUT/'precision_recall_curve.csv',index=False)
    plt.figure(figsize=(7,4));plt.plot(r,p,label=f'Isolation Forest: AP={ap:.3f}');plt.axhline(test.SCENARIO_LABEL.mean(),color='grey',linestyle='--',label='Injected-case prevalence');plt.xlabel('Recall of synthetic injected cases');plt.ylabel('Precision against synthetic labels');plt.title('Untouched time test: May–June 2025');plt.legend();plt.tight_layout();plt.savefig(OUT/'precision_recall.png',dpi=160);plt.close()
    metrics[metrics.SPLIT.eq('TEST')].plot(x='POLICY_ID',y=['TP','FP','FN'],kind='bar',figsize=(8,4),title='Test threshold sensitivity — synthetic cases')
    plt.ylabel('Transactions');plt.tight_layout();plt.savefig(OUT/'threshold_tradeoff.png',dpi=160);plt.close()
    with sqlite3.connect(OUT/'risk_warehouse.sqlite') as db:
        for n,frame in {**frames,'TRANSACTION_RISK':f,'THRESHOLD_METRICS':metrics}.items():frame.to_sql(n,db,if_exists='replace',index=False)
        db.executescript((ROOT/'sql/01_transformations.sql').read_text())
        sqlchecks=json.loads((ROOT/'sql/checks.json').read_text())
        for name,query in sqlchecks.items():
            bad=pd.read_sql_query(query,db)
            if len(bad):raise ValueError(f'SQL check {name}: {len(bad)} failure rows')
            checks['SQL_'+name]=True
        joined=pd.read_sql_query('SELECT * FROM V_RISK_DETAIL',db)
        summary=pd.read_sql_query('SELECT * FROM V_DAILY_RISK',db)
        if len(joined)!=len(f) or not np.isclose(joined.AMOUNT_GBP.sum(),f.AMOUNT_GBP.sum(),atol=.01,rtol=0):raise ValueError('Join fanout / amount reconciliation')
        if int(summary.ALERT_COUNT.sum())!=int(f.ALERT_FLAG.sum()):raise ValueError('Alert reconciliation')
        summary.to_csv(PROCESSED/'DAILY_RISK.csv',index=False)
        # HANA-style SELECT bodies are logical smoke-tested, not tenant-validated.
        for path in sorted((ROOT/'datasphere').glob('*.sql')):
            body=path.read_text().strip().rstrip(';')
            if path.stem not in ['V_RISK_DETAIL','V_DAILY_RISK']:
                db.execute(f'DROP VIEW IF EXISTS "{path.stem}"')
                db.execute(f'CREATE VIEW "{path.stem}" AS '+body)
            pd.read_sql_query(f'SELECT * FROM "{path.stem}" LIMIT 5',db)
    # Retrieve serialised CSV and reconcile what users actually upload.
    uploaded=pd.read_csv(PROCESSED/'TRANSACTION_RISK.csv')
    if not np.array_equal(uploaded.ALERT_FLAG, (uploaded.ANOMALY_SCORE>=round(threshold,10)).astype(int)):raise ValueError('CSV score threshold precision')
    checks['join_grain_and_amount_reconciled']=True
    checks['daily_alert_totals_reconciled']=True
    checks['csv_threshold_precision']=True
    metadata={'seed':42,'features':FEATURES,'default_policy':'Q98','thresholds':thresholds,'model_parameters':model.get_params(),'test_average_precision_synthetic':float(ap),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__},'training':'2025-01-01 through 2025-03-31','validation':'2025-04-01 through 2025-04-30','test':'2025-05-01 through 2025-06-29','score_definition':'negative IsolationForest.score_samples; NOT probability'}
    (OUT/'model_metadata.json').write_text(json.dumps(metadata,indent=2))
    (OUT/'validation.json').write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2))
    default=metrics[(metrics.SPLIT=='TEST') & (metrics.POLICY_ID=='Q98')].iloc[0]
    (OUT/'RUN_SUMMARY.md').write_text(f'''# Verified local run\n\nSynthetic educational demonstration. No confirmed fraud outcomes.\n\n- Transactions: {len(f):,}; accounts: {len(frames['ACCOUNTS'])}; merchants: {len(frames['MERCHANTS'])}.\n- Total payment value: GBP {f.AMOUNT_GBP.sum():,.2f}.\n- Default Q98 threshold: {threshold:.10f}.\n- All-period alerts: {f.ALERT_FLAG.sum():,}.\n- Test transactions: {len(test):,}; injected cases: {test.SCENARIO_LABEL.sum():,}.\n- Test default alerts: {int(default.ALERT_COUNT)}; TP={int(default.TP)}, FP={int(default.FP)}, FN={int(default.FN)}, TN={int(default.TN)}.\n- Test synthetic precision: {default.PRECISION:.3f}; recall: {default.RECALL:.3f}; average precision: {ap:.3f}.\n- {len(checks)} validation checks passed.\n\nThese metrics measure recovery of the generator's scenarios, not fraud performance. See MODEL_CARD.md and threshold table before interpreting them. Python and SQLite verified; SAP tenant deployment is manual and unverified here.\n''')
    print(f'SUCCESS: {len(f):,} transactions; {len(checks)} checks passed.')
    print('Next: open outputs/RUN_SUMMARY.md, then docs/02_DATASPHERE.md')


if __name__=='__main__':
    main('--regenerate' in sys.argv)
