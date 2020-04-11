import models
import settings
from tqdm import tqdm
from functools import reduce


def main(file_in, file_answer):
    model = models.TrigramModel()
    inputs = [line.strip() for line in open(file_in) if line.strip()]
    results = [model.predict(line) for line in tqdm(inputs)]
    answers = [line.strip() for line in open(file_answer) if line.strip()]
    char_count, char_correct = 0, 0
    line_count, line_correct = 0, len(results)
    for result, ans in zip(results, answers):
        char_count += len(result)
        char_correct += reduce(lambda a, b: a + (b[0] == b[1]), zip(results, ans))
        line_correct += result == ans
    print(model.smooth_1, model.smooth_2, char_correct / char_count, line_correct / line_count)


if __name__ == '__main__':
    main(settings.input_file, settings.answer_file)
