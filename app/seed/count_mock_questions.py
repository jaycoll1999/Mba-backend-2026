import re
from collections import Counter

with open(r'd:\MBA_Project_2026\frontend\src\api\mockQuestions.ts', 'r', encoding='utf-8') as f:
    text = f.read()

questions = re.findall(r"id:\s*['\"](q-[^'\"]+)['\"]", text)
print('Total questions in mockQuestions.ts:', len(questions))

subjects = re.findall(r"subjectName:\s*['\"]([^'\"]+)['\"]", text)
print('Subject counts in mockQuestions:')
for k, v in Counter(subjects).items():
    print(f'  {k}: {v}')

diffs = re.findall(r"difficulty:\s*['\"]([^'\"]+)['\"]", text)
print('Difficulty counts in mockQuestions:')
for k, v in Counter(diffs).items():
    print(f'  {k}: {v}')
