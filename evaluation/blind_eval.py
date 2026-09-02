#!/usr/bin/env python3
"""Prepare and score an external three-arm reader test. Does not generate fiction."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ARMS = ('original', 'profile_guided', 'no_profile')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def prepare(experiment, seed=0, max_length_ratio=1.25):
    if not math.isfinite(max_length_ratio) or max_length_ratio < 1:
        raise ValueError('max_length_ratio 必须是至少 1 的有限数值')
    if not isinstance(experiment, dict) or experiment.get('schema_version') != '1.0':
        raise ValueError('实验 schema_version 必须为 1.0')
    if not isinstance(experiment.get('experiment_id'), str) or not experiment['experiment_id'].strip():
        raise ValueError('缺少 experiment_id')
    readers = experiment.get('reader_ids', [])
    if not isinstance(readers, list) or not readers or any(not isinstance(r, str) or not r.strip() for r in readers) or len(set(readers)) != len(readers):
        raise ValueError('reader_ids 必须非空、唯一，使用匿名编号')
    items = experiment.get('items', [])
    if not isinstance(items, list) or not items:
        raise ValueError('缺少匹配的三组文本')
    item_ids = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('item_id'), str) or not item['item_id'].strip() or item['item_id'] in item_ids:
            raise ValueError('item_id 必须非空且唯一')
        item_ids.add(item['item_id'])
        for field in ('facts', 'cue_audit', 'original_source', 'profile_sha256', 'generation_settings'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"{item['item_id']} 缺少 {field}")
        candidates = item.get('candidates', {})
        if not isinstance(candidates, dict) or set(candidates) != set(ARMS):
            raise ValueError('每项必须恰有 original/profile_guided/no_profile 三组')
        lengths, texts = [], []
        for arm in ARMS:
            candidate = candidates[arm]
            if not isinstance(candidate, dict) or candidate.get('facts_sha256') != digest(item['facts']):
                raise ValueError('三组必须绑定同一事实梗概')
            text = candidate.get('text')
            if not isinstance(text, str) or not text.strip():
                raise ValueError('候选文本不能为空')
            lengths.append(len(''.join(text.split())))
            texts.append(text)
        if len(set(texts)) != 3:
            raise ValueError('三组文本不能完全相同')
        if max(lengths) / min(lengths) > max_length_ratio:
            raise ValueError('三组文本篇幅差异超出预先设定的上限')
    rng = random.Random(seed)
    trials, private = [], []
    number = 0
    for reader in readers:
        ordered = list(items)
        rng.shuffle(ordered)
        for item in ordered:
            number += 1
            trial_id = f'T{number:06d}'
            arms = list(ARMS)
            rng.shuffle(arms)
            mapping = dict(zip(('A', 'B', 'C'), arms))
            trials.append({'trial_id': trial_id, 'reader_id': reader,
                'candidates': {label: item['candidates'][arm]['text'] for label, arm in mapping.items()}})
            private.append({'trial_id': trial_id, 'reader_id': reader, 'item_id': item['item_id'], 'mapping': mapping})
    blind = {'schema_version': '1.0', 'experiment_id': experiment['experiment_id'],
        'question': '哪一段最像目标作者的原文？请选择 A、B 或 C；不要检索原文。', 'trials': trials}
    key = {'schema_version': '1.0', 'experiment_id': experiment['experiment_id'], 'seed': seed,
        'max_length_ratio': max_length_ratio, 'input_sha256': digest(experiment),
        'blind_sha256': digest(blind), 'trials': private}
    return blind, key


def score(blind, key, responses):
    if digest(blind) != key.get('blind_sha256') or blind.get('experiment_id') != key.get('experiment_id'):
        raise ValueError('盲测文本或实验编号与答案表不一致')
    trials = {trial['trial_id']: trial for trial in key['trials']}
    if len(trials) != len(key['trials']):
        raise ValueError('答案表存在重复 trial_id')
    seen, counts = set(), dict.fromkeys(ARMS, 0)
    per_reader, per_item = {}, {}
    for response in responses:
        if not isinstance(response, dict):
            raise ValueError('答卷必须是 JSON 对象')
        trial_id = response.get('trial_id')
        if trial_id not in trials or trial_id in seen:
            raise ValueError('未知或重复 trial_id')
        trial = trials[trial_id]
        if response.get('reader_id') != trial['reader_id'] or response.get('choice') not in trial['mapping']:
            raise ValueError('读者编号或选项不匹配')
        seen.add(trial_id)
        arm = trial['mapping'][response['choice']]
        counts[arm] += 1
        for table, group in ((per_reader, trial['reader_id']), (per_item, trial['item_id'])):
            table.setdefault(group, dict.fromkeys(ARMS, 0))[arm] += 1
    count = len(seen)
    rates = {arm: counts[arm] / count if count else None for arm in ARMS}
    return {'schema_version': '1.0', 'experiment_id': blind['experiment_id'],
        'status': 'complete' if count == len(trials) else 'incomplete',
        'received_trials': count, 'expected_trials': len(trials), 'missing_trial_ids': sorted(set(trials) - seen),
        'selected_as_original_count': counts, 'selected_as_original_rate': rates,
        'profile_minus_baseline_rate': rates['profile_guided'] - rates['no_profile'] if count else None,
        'by_reader': per_reader, 'by_item': per_item,
        'interpretation': '描述性选择率，不是作者相似度；重复读者和场景不独立，不自动给显著性或成功结论。'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_parser = sub.add_parser('prepare')
    prepare_parser.add_argument('experiment', type=Path)
    prepare_parser.add_argument('--blind', type=Path, required=True)
    prepare_parser.add_argument('--key', type=Path, required=True)
    prepare_parser.add_argument('--seed', type=int, default=0)
    prepare_parser.add_argument('--max-length-ratio', type=float, default=1.25)
    score_parser = sub.add_parser('score')
    score_parser.add_argument('--blind', type=Path, required=True)
    score_parser.add_argument('--key', type=Path, required=True)
    score_parser.add_argument('--responses', type=Path, required=True)
    score_parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    def read(path):
        return json.loads(path.read_text(encoding='utf-8-sig'))
    try:
        if args.command == 'prepare':
            if len({p.resolve() for p in (args.experiment, args.blind, args.key)}) != 3:
                raise ValueError('实验输入、盲测文本与答案表必须使用不同路径')
            blind, key = prepare(read(args.experiment), args.seed, args.max_length_ratio)
            outputs = ((args.blind, blind), (args.key, key))
        else:
            if args.output.resolve() in {p.resolve() for p in (args.blind, args.key, args.responses)}:
                raise ValueError('评分输出不能覆盖输入文件')
            responses = [json.loads(line) for line in args.responses.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            outputs = ((args.output, score(read(args.blind), read(args.key), responses)),)
        for path, value in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
