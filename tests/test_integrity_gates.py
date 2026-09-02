from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import analyze_style
import corpus_index
import render_profile
import validate_bundle
import validate_profile
from test_validate_bundle import bundle_artifacts


def render(root, profile, evidence, metrics):
    corpus_index.write_json(metrics, root / 'style-metrics.json')
    profile['surface_ranges']['metrics_sha256'] = corpus_index.file_sha256(root / 'style-metrics.json')
    profile['analysis_saturation']['ledger_sha256'] = corpus_index.file_sha256(root / 'sampling-ledger.json')
    (root / 'style-metrics.md').write_text(analyze_style.render_markdown(metrics), encoding='utf-8')
    (root / 'author-analysis.md').write_text(render_profile.render_analysis(profile, evidence), encoding='utf-8')
    (root / 'writing-packet.md').write_text(render_profile.render_packet(profile, evidence), encoding='utf-8')


def check(root, profile, evidence, records, **kwargs):
    return validate_bundle.validate_bundle(profile, evidence, records,
        root / 'manifest.json', root / 'sampling-ledger.json', root / 'style-metrics.json',
        root / 'style-metrics.md', root / 'author-analysis.md', root / 'writing-packet.md',
        root / 'corpus-index.jsonl', **kwargs)


def separated_bundle(root):
    profile, evidence, _, _, _ = bundle_artifacts(root)
    source = root / 'W03.txt'
    source.write_text('他站在窗前。\n\n她转身离开。', encoding='utf-8')
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['sources'].append({'path': 'W03.txt', 'work_id': 'W03', 'period': '', 'metadata': {},
        'segments': [{'paragraph_start': 1, 'paragraph_end': 2, 'sample_id': 'S03',
            'chapter_id': 'C01', 'scene_id': 'SC03', 'scene_type': 'confrontation', 'holdout': True}]})
    corpus_index.write_json(manifest, manifest_path)
    with redirect_stdout(io.StringIO()):
        code = corpus_index.main(['prepare', str(root / 'W01.txt'), str(root / 'W02.txt'), str(source),
            '--manifest', str(manifest_path), '--analysis-index', str(root / 'corpus-index.jsonl'),
            '--holdout-index', str(root / 'holdout-index.jsonl'), '--commitment', str(root / 'commitment.json'),
            '--ledger', str(root / 'sampling-ledger.json'), '--budget', '3'])
    assert code == 0
    records = corpus_index.read_jsonl(root / 'corpus-index.jsonl')
    holdout = corpus_index.read_jsonl(root / 'holdout-index.jsonl')
    ledger = corpus_index.read_ledger(root / 'sampling-ledger.json')
    corpus_index.mark_ledger(ledger, [r['chunk_id'] for r in records], 'analyzed', '精读完成')
    corpus_index.write_json(ledger, root / 'sampling-ledger.json')
    profile['corpus'].update(work_ids=['W01', 'W02', 'W03'], sample_ids=['S01', 'S02', 'S03'],
        source_hashes=sorted({r['source_sha256'] for r in records + holdout}), holdout_sample_ids=['S03'],
        manifest_sha256=corpus_index.file_sha256(manifest_path))
    for item in evidence:
        record = next(r for r in records if r['work_id'] == item['work_id'])
        item['chunk_id'] = record['chunk_id']
    corpus_index.write_json(profile, root / 'provisional-profile.json')
    with redirect_stdout(io.StringIO()):
        code = corpus_index.main(['reveal-holdout', '--holdout-index', str(root / 'holdout-index.jsonl'),
            '--commitment', str(root / 'commitment.json'), '--provisional-profile', str(root / 'provisional-profile.json'),
            '--output', str(root / 'reveal.json')])
    assert code == 0
    profile['corpus']['provisional_profile_sha256'] = corpus_index.file_sha256(root / 'provisional-profile.json')
    record = holdout[0]
    holdout_evidence = {**evidence[0], 'evidence_id': 'EH01', 'evidence_role': 'holdout',
        'evaluation_outcome': 'matched', 'excerpt': '他站在窗前。', 'sample_id': 'S03'}
    for field in ('work_id', 'source_path', 'source_sha256', 'chunk_id', 'paragraph_start', 'paragraph_end',
                  'content_char_start', 'content_char_end'):
        holdout_evidence[field] = record[field]
    evidence.append(holdout_evidence)
    profile['rules'][0]['evidence_ids'].append('EH01')
    profile['rules'][0]['holdout_status'] = 'passed'
    profile['rules'][0]['holdout_evaluation'].update(eligible=1, matched=1)
    next(entry for entry in profile['coverage'] if entry['dimension'] == profile['rules'][0]['dimension'])['evidence_count'] = 4
    metrics = analyze_style.build_report_from_index(root / 'corpus-index.jsonl')
    render(root, profile, evidence, metrics)
    kwargs = dict(holdout_index_records=holdout, holdout_index_path=root / 'holdout-index.jsonl',
        holdout_commitment_path=root / 'commitment.json', holdout_reveal_path=root / 'reveal.json',
        provisional_profile_path=root / 'provisional-profile.json')
    return profile, evidence, records, metrics, kwargs


class IntegrityGatesTests(unittest.TestCase):
    def test_render_and_validate_complete_holdout_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, kwargs = separated_bundle(root)
            corpus_index.write_json(profile, root / 'author-profile.json')
            corpus_index.write_jsonl(evidence, root / 'evidence-map.jsonl')
            (root / 'analysis-narrative.md').write_text('## 跨维度综合\n\nR01 与 E0001：先动作后判断，保留知识边界。', encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(render_profile.main([str(root / 'author-profile.json'), '--evidence', str(root / 'evidence-map.jsonl'),
                    '--narrative', str(root / 'analysis-narrative.md'), '--analysis', str(root / 'author-analysis.md'),
                    '--packet', str(root / 'writing-packet.md')]), 0)
                self.assertEqual(validate_bundle.main([str(root / 'author-profile.json'), '--evidence', str(root / 'evidence-map.jsonl'),
                    '--index', str(root / 'corpus-index.jsonl'), '--manifest', str(root / 'manifest.json'),
                    '--ledger', str(root / 'sampling-ledger.json'), '--metrics', str(root / 'style-metrics.json'),
                    '--metrics-markdown', str(root / 'style-metrics.md'), '--analysis', str(root / 'author-analysis.md'),
                    '--packet', str(root / 'writing-packet.md'), '--holdout-index', str(kwargs['holdout_index_path']),
                    '--holdout-commitment', str(kwargs['holdout_commitment_path']), '--holdout-reveal', str(kwargs['holdout_reveal_path']),
                    '--provisional-profile', str(kwargs['provisional_profile_path'])]), 0)
            text = (root / 'writing-packet.md').read_text(encoding='utf-8')
            self.assertIn(profile['rules'][0]['action'], text)
            self.assertIn(evidence[0]['excerpt'], text)

    def test_forged_index_text_detected_despite_updated_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, ledger, _ = bundle_artifacts(root)
            records[0]['text'] += '\n伪造的另一句话。'
            corpus_index.write_jsonl(records, root / 'corpus-index.jsonl')
            ledger['index_sha256'] = corpus_index.file_sha256(root / 'corpus-index.jsonl')
            corpus_index.write_json(ledger, root / 'sampling-ledger.json')
            metrics = analyze_style.build_report_from_index(root / 'corpus-index.jsonl')
            render(root, profile, evidence, metrics)
            self.assertTrue(any('text 与来源重建结果不一致' in e for e in check(root, profile, evidence, records)))

    def test_forged_metrics_detected_despite_updated_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, metrics = bundle_artifacts(root)
            metrics['aggregate']['sentence_length']['median'] = 999
            metrics['report_sha256'] = analyze_style.report_sha256(metrics)
            render(root, profile, evidence, metrics)
            self.assertTrue(any('重新计算结果不一致' in e for e in check(root, profile, evidence, records)))

    def test_insufficient_dimension_cannot_disappear_from_unresolved(self):
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records, _, _ = bundle_artifacts(Path(folder))
            profile['coverage'][0].update(status='insufficient', uncovered=['缺少行动场景'])
            self.assertTrue(any('insufficient 维度必须列入' in e for e in validate_profile.validate_profile(profile, evidence, records)))

    def test_separated_holdout_cli_bundle_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, metrics, kwargs = separated_bundle(root)
            self.assertEqual(check(root, profile, evidence, records, **kwargs), [])
            self.assertNotIn('他站在窗前', (root / 'corpus-index.jsonl').read_text(encoding='utf-8'))
            self.assertNotIn('他站在窗前', (root / 'commitment.json').read_text(encoding='utf-8'))
            self.assertEqual(len(metrics['sources']), 2)
            self.assertEqual(metrics['input_mode'], 'analysis_index')

    def test_post_reveal_rule_change_invalidates_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, metrics, kwargs = separated_bundle(root)
            profile['rules'][0]['trigger'] = '看过答案后放宽条件'
            render(root, profile, evidence, metrics)
            self.assertTrue(any('解封后改变' in e for e in check(root, profile, evidence, records, **kwargs)))

    def test_provisional_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, kwargs = separated_bundle(root)
            corpus_index.write_json(profile, root / 'provisional-profile.json')
            self.assertTrue(any('初稿已变化' in e for e in check(root, profile, evidence, records, **kwargs)))

    def test_partial_holdout_outcomes_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, kwargs = separated_bundle(root)
            profile['corpus']['sample_ids'].append('S04')
            profile['corpus']['holdout_sample_ids'].append('S04')
            self.assertTrue(any('每个留出样本' in e for e in validate_profile.validate_profile(
                profile, evidence, records, holdout_index_records=kwargs['holdout_index_records'])))

    def test_holdout_leakage_and_full_source_metrics_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, kwargs = separated_bundle(root)
            metrics = analyze_style.build_report([root / 'W01.txt', root / 'W02.txt', root / 'W03.txt'])
            render(root, profile, evidence, metrics)
            self.assertTrue(any('不能读取完整来源正文' in e for e in check(root, profile, evidence, records, **kwargs)))
            leaked = records + kwargs['holdout_index_records']
            self.assertTrue(any('分析索引不能包含留出正文' in e for e in validate_profile.validate_profile(
                profile, evidence, leaked, holdout_index_records=kwargs['holdout_index_records'])))
            with self.assertRaisesRegex(ValueError, '留出正文'):
                analyze_style.build_report_from_index(root / 'holdout-index.jsonl')

    def test_stub_or_stale_markdown_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, _ = bundle_artifacts(root)
            path = root / 'author-analysis.md'
            path.write_text(render_profile.artifact_header('author-analysis', profile, evidence) + '\nprofile-test R01', encoding='utf-8')
            self.assertTrue(any('完整标准分析正文' in e for e in check(root, profile, evidence, records)))
            (root / 'style-metrics.md').write_text('占位', encoding='utf-8')
            self.assertTrue(any('style-metrics.md' in e for e in check(root, profile, evidence, records)))

    def test_unreviewed_dimensions_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records, _, _ = bundle_artifacts(Path(folder))
            profile['coverage'][0]['reviewed_sample_ids'] = []
            self.assertTrue(any('reviewed_sample_ids' in e or '实际审阅' in e for e in validate_profile.validate_profile(profile, evidence, records)))

    def test_non_metric_pointer_and_unexplained_pointer_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, metrics = bundle_artifacts(root)
            rule = profile['rules'][0]
            rule['metric_refs'] = ['/schema_version']
            rule['metric_claims'] = [{'ref': '/schema_version', 'interpretation': '错误引用版本号'}]
            render(root, profile, evidence, metrics)
            self.assertTrue(any('只能指向' in e for e in check(root, profile, evidence, records)))
            rule['metric_refs'] = ['/aggregate/dialogue/content_ratio']
            rule['metric_claims'] = []
            self.assertTrue(any('metric_claims' in e for e in check(root, profile, evidence, records)))

    def test_high_confidence_without_holdout_or_full_corpus_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            profile, evidence, records, _, _ = bundle_artifacts(Path(folder))
            profile['analysis_saturation']['status'] = 'limited'
            profile['rules'][0]['confidence'] = 'high'
            self.assertTrue(any('high 可信度' in e for e in validate_profile.validate_profile(profile, evidence, records)))

    def test_real_extend_round_bound_to_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile, evidence, records, _, metrics = bundle_artifacts(root)
            ledger = corpus_index.build_sampling_ledger(records, corpus_index.file_sha256(root / 'corpus-index.jsonl'), budget=1, holdout_ratio=0)
            selected = {item['chunk_id'] for item in ledger['items']}
            corpus_index.mark_ledger(ledger, list(selected), 'analyzed', '初读')
            extra = next(r for r in records if r['chunk_id'] not in selected)
            corpus_index.extend_ledger(ledger, records, [extra['chunk_id']], '补读')
            sequence = ledger['updates'][-1]['sequence']
            corpus_index.mark_ledger(ledger, [extra['chunk_id']], 'analyzed', '补读完成')
            corpus_index.write_json(ledger, root / 'sampling-ledger.json')
            profile['analysis_saturation']['rounds'] = [{'round_id': 'SAT01', 'ledger_update_sequences': [sequence],
                'added_sample_ids': extra['sample_ids'], 'new_rule_count': 0, 'new_counterexample_count': 0,
                'unresolved_dimension_ids': [], 'note': '补读未新增'}]
            render(root, profile, evidence, metrics)
            self.assertEqual(check(root, profile, evidence, records), [])
            profile['analysis_saturation']['rounds'][0]['ledger_update_sequences'] = [1]
            self.assertTrue(any('有效 extend' in e for e in check(root, profile, evidence, records)))


if __name__ == '__main__':
    unittest.main()
