import models
import os
import settings
from tqdm import tqdm
from functools import reduce


def run_batch():
    for i in range(2, 12, 2):
        for j in range(12, 22, 2):
            script = """tmux new-session "
            export INPUT_METHOD_SMOOTH_1=0.%02d;
            export INPUT_METHOD_SMOOTH_2=0.%02d;
            python main.py > result/%d_%d;
            "
            """
            os.system(script)


def main(file_in, file_answer):
    model = models.TrigramModel()
    inputs = [line.strip() for line in open(file_in) if line.strip()]
    results = [model.predict(line) for line in tqdm(inputs)]
    answers = [line.strip() for line in open(file_answer) if line.strip()]
    char_count, char_correct = 0, 0
    line_count, line_correct = len(results), 0
    for result, ans in zip(results, answers):
        char_count += len(result)
        char_correct += reduce(lambda a, b: a + (b[0] == b[1]), zip(results, ans), 0)
        line_correct += result == ans
    print(model.smooth_1, model.smooth_2, char_correct / char_count, line_correct / line_count)


if __name__ == '__main__':
    main(settings.input_file, settings.answer_file)
