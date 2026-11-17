import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.claude/lib'))
from avs import POLICY, identify_policy_outliers, infer_tiktok_format, score_post


class EvidenceScoringTests(unittest.TestCase):
    def test_supplied_weights_and_unassigned_youtube_share(self):
        self.assertEqual(POLICY['weights']['instagram_unconnected']['sends'], .30)
        self.assertEqual(POLICY['weights']['linkedin']['dwell'], .34)
        for profile, weights in POLICY['weights'].items():
            self.assertAlmostEqual(sum(weights.values()), .9 if profile == 'youtube_longform' else 1)

    def test_missing_is_not_zero_and_partial_is_not_renormalized(self):
        result = score_post({'reach': 1000, 'likesCount': 100}, 'instagram')
        self.assertIsNone(result['score'])
        self.assertEqual(result['coverage'], .06)
        self.assertAlmostEqual(result['observed_contribution'], .6)
        self.assertIn('completion', result['missing'])

    def test_zero_stays_zero(self):
        result = score_post({'reach': 100, 'sendCount': 0, 'sharesCount': 20}, 'instagram')
        self.assertEqual(result['signals']['sends'], 0)

    def test_public_shares_are_not_private_sends(self):
        result = score_post({'reach': 100, 'sharesCount': 20}, 'instagram')
        self.assertIsNone(result['signals']['sends'])
        self.assertIsNone(result['observed_contribution'])

    def test_followers_never_replace_exposure(self):
        self.assertIsNone(score_post({'ownerFollowersCount': 100, 'likesCount': 10}, 'instagram')['signals']['likes'])

    def test_total_comments_are_not_substantive_or_dwell(self):
        result = score_post({'Impressions': 100, 'Comments': 20, 'Clicks': 20}, 'linkedin')
        self.assertIsNone(result['signals']['substantive_comments'])
        self.assertIsNone(result['signals']['dwell'])

    def test_x_public_reply_and_bookmark_counts_keep_private_evidence_missing(self):
        result = score_post({'viewCount': 1000, 'replyCount': 20,
                             'bookmarkCount': 30, 'likeCount': 100}, 'x')
        self.assertEqual(result['signals']['comments'], .02)
        self.assertEqual(result['signals']['saves'], .03)
        self.assertEqual(result['signals']['likes'], .1)
        self.assertAlmostEqual(result['observed_contribution'], 1.38)
        self.assertEqual(result['coverage'], .44)
        self.assertIsNone(result['signals']['author_replies'])
        self.assertIsNone(result['signals']['dwell'])
        self.assertIsNone(result['score'])
        self.assertEqual(result['status'], 'partial_evidence')

    def test_invalid_values_do_not_pass(self):
        for value in [True, -1, float('nan'), float('inf'), 65, '65%', 'unknown']:
            self.assertIsNone(score_post({'signals': {'completion': value}}, 'tiktok')['signals']['completion'])

    def test_complete_explicit_normalized_signals(self):
        signals = {name: .5 for name in POLICY['weights']['tiktok']}
        result = score_post({'signals': signals}, 'tiktok')
        self.assertEqual(result['score'], 50)
        self.assertEqual(result['missing'], [])

    def test_longform_incomplete_policy_is_never_rescaled(self):
        signals = {name: 1 for name in POLICY['weights']['youtube_longform']}
        result = score_post({'format': 'longform', 'signals': signals}, 'youtube')
        self.assertIsNone(result['score'])
        self.assertEqual(result['observed_contribution'], 90)
        self.assertEqual(result['unassigned_weight'], .1)

    def test_no_outlier_from_one_record(self):
        self.assertEqual(identify_policy_outliers([{'reach': 10, 'likesCount': 10}], 'instagram'), [])

    def test_outliers_compare_same_coverage(self):
        posts = [{'reach': 100, 'likesCount': n, 'format': 'image'} for n in [1]*9+[90]]
        posts.append({'reach': 100, 'sendCount': 100, 'format': 'image'})
        selected = identify_policy_outliers(posts, 'instagram')
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['likesCount'], 90)
        self.assertEqual(selected[0]['_comparison_count'], 10)
        self.assertIsNone(selected[0]['_engagement_score'])

    def test_export_formats_are_separate_cohorts(self):
        posts = [{"Impressions": 100, "Likes": 1, "Post Type": "text"} for _ in range(9)]
        posts.append({"Impressions": 100, "Likes": 99, "Content Type": "document"})
        self.assertEqual(identify_policy_outliers(posts, "linkedin"), [])

    def test_unknown_format_not_claimed_as_comparable(self):
        posts = [{"reach": 100, "likesCount": n} for n in [1]*9+[99]]
        self.assertEqual(identify_policy_outliers(posts, "instagram"), [])

    def test_youtube_requires_format(self):
        self.assertEqual(score_post({'statistics': {'viewCount': 1000}}, 'youtube')['status'], 'missing_format')

    def test_fetched_tiktok_format_preserves_video_and_slideshow_evidence(self):
        records = []
        for likes in [1]*9+[90]:
            raw = {'diggCount': likes, 'playCount': 100, 'videoMeta': {'duration': 20}}
            records.append({'diggCount': raw['diggCount'], 'playCount': raw['playCount'],
                            'format': infer_tiktok_format(raw)})
        selected = identify_policy_outliers(records, 'tiktok')
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['diggCount'], 90)
        self.assertEqual(infer_tiktok_format({'isSlideshow': True, 'videoMeta': {'duration': 20}}), 'slideshow')
        self.assertEqual(infer_tiktok_format({'type': 'photo'}), 'photo')
        self.assertIsNone(infer_tiktok_format({'playCount': 100, 'videoMeta': {}}))
        self.assertEqual(identify_policy_outliers([dict(row, format='unknown') for row in records], 'tiktok'), [])

    def test_analyzer_cli_contracts(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / 'in.json'
            source.write_text(json.dumps([{'reach': 100, 'views': 100, 'Impressions': 100,
                                           'likesCount': 5, 'likes': 5, 'text': 'operator', 'caption': 'operator'}]))
            for platform in ['instagram', 'tiktok', 'x', 'linkedin']:
                output = folder / (platform+'.json')
                script = ROOT / f'.claude/skills/{platform}-research/scripts/analyze_posts.py'
                result = subprocess.run([sys.executable, str(script), '--input', str(source), '--output', str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(output.read_text())
                self.assertEqual(report['outlier_count'], 0)
                self.assertIsNone(report['evidence'][0]['score'])

    def test_csv_json_linkedin_equivalence(self):
        script = ROOT / '.claude/skills/linkedin-research/scripts/analyze_posts.py'
        spec = importlib.util.spec_from_file_location('linkedin_test', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            csv = Path(folder)/'data.csv'
            csv.write_text('Impressions,Reactions,Comments\n100,0,2\n')
            record = module.load_linkedin_records(str(csv))[0]
            self.assertEqual(score_post(record, 'linkedin')['signals'], score_post({'Impressions':100,'Reactions':0,'Comments':2},'linkedin')['signals'])


class CanonicalWrapperTests(unittest.TestCase):
    def test_qa_forwards_exact_input_without_inventing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cli = root/'skills/social-data-calibrator/cli.py'
            cli.parent.mkdir(parents=True)
            cli.write_text('import json,sys\nfrom pathlib import Path\np=Path(sys.argv[sys.argv.index("--input")+1])\nprint(json.dumps({"argv":sys.argv[1:],"payload":json.loads(p.read_text())}))\n')
            payload = root/'draft.json'
            payload.write_text('{"content":"Verified story","platform":"instagram"}')
            wrapper = ROOT/'.claude/skills/content-qa-gate/scripts/run_qa_gate.py'
            result = subprocess.run([sys.executable,str(wrapper),'qa','--input',str(payload),'--canonical-root',str(root)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            receipt=json.loads(result.stdout)
            self.assertEqual(receipt['payload'],json.loads(payload.read_text()))
            self.assertEqual(receipt['argv'][0],'qa-gate')
            self.assertNotIn('--duration',receipt['argv'])

    def test_calibrator_stages_nested_files_and_requires_manifest_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            cli=root/'skills/social-data-calibrator/cli.py';cli.parent.mkdir(parents=True)
            cli.write_text("import json,sys\nfrom pathlib import Path\nd=Path(sys.argv[sys.argv.index('--auto-dir')+1])\nif sys.argv[1]=='ingest':\n (d/'ingest_manifest.json').write_text(json.dumps({'files':[{'file':p.name} for p in d.iterdir() if p.suffix=='.csv']}))\nelse:\n (d/'calibration_report_2026.json').write_text('{}')\n")
            exports=root/'exports';(exports/'nested').mkdir(parents=True)
            (exports/'nested/posts.csv').write_text('views\n1\n')
            wrapper=ROOT/'.claude/skills/historical-calibrator/scripts/calibrate_exports.py'
            run=root/'run'
            command=[sys.executable,str(wrapper),'--export-dir',str(exports),'--run-dir',str(run),'--canonical-root',str(root)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((run/'inputs/posts.csv').exists())
            receipt=json.loads((run/'provenance.json').read_text())
            self.assertEqual(receipt['inputs'][0]['relative_path'],'nested/posts.csv')
            self.assertEqual(receipt['status'],'analysis_completed_provenance_review_required')
            cli.write_text("import json,sys\nfrom pathlib import Path\nd=Path(sys.argv[sys.argv.index('--auto-dir')+1])\n(d/'ingest_manifest.json').write_text('{\"files\":[]}')\n")
            command[command.index(str(run))]=str(root/'run2')
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(json.loads((root/'run2/provenance.json').read_text())['status'],'ingest_coverage_unverified')

    def test_calibrator_refuses_existing_run_before_external_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            cli=root/'skills/social-data-calibrator/cli.py';cli.parent.mkdir(parents=True);cli.write_text('raise RuntimeError("must not run")')
            exports=root/'exports';exports.mkdir();(exports/'posts.csv').write_text('views\n1\n')
            run=root/'run';run.mkdir();sentinel=run/'sentinel';sentinel.write_text('keep')
            wrapper=ROOT/'.claude/skills/historical-calibrator/scripts/calibrate_exports.py'
            result=subprocess.run([sys.executable,str(wrapper),'--export-dir',str(exports),'--run-dir',str(run),'--canonical-root',str(root)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(sentinel.read_text(),'keep')
            self.assertNotIn('must not run',result.stderr)


if __name__=='__main__':
    unittest.main()
