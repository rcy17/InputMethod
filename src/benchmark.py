import os
from . import settings, models
from tqdm import tqdm
from functools import reduce


def run_batch():
    for i in range(3, 7):
        for j in range(16, 20):
            script = """tmux new-window "
            export INPUT_METHOD_SMOOTH_1=0.%02d;
            export INPUT_METHOD_SMOOTH_2=0.%02d;
            python benchmark.py > result/%d_%d;
            "
            """ % (i, j, i, j)
            os.system(script)


def run_batch_binary():
    for i in range(100, 68, -2):
        script = """tmux new-window "
        export INPUT_METHOD_SMOOTH=%.2f;
        export USE_BINARY_MODEL=1;
        python benchmark.py > result/%d;
        "
        """ % (i / 100, i)
        os.system(script)


def main(file_in, file_answer, model_class):
    model = model_class()
    inputs = [line.strip() for line in open(file_in) if line.strip()]
    results = [model.predict(line) for line in tqdm(inputs)]
    answers = [line.strip() for line in open(file_answer) if line.strip()]
    char_count, char_correct = 0, 0
    line_count, line_correct = len(results), 0
    for result, ans in zip(results, answers):
        char_count += len(result)
        char_correct += reduce(lambda a, b: a + (b[0] == b[1]), zip(result, ans), 0)
        line_correct += result == ans
    if model_class == models.TrigramModel:
        print(model.smooth_1, model.smooth_2, char_correct / char_count, line_correct / line_count)
    else:
        print(model.smooth, char_correct / char_count, line_correct / line_count)


if __name__ == '__main__':
    main(settings.input_file, settings.answer_file,
         models.PinyinBinaryModel if settings.use_binary else models.TrigramModel)
