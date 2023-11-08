def main():
    with open('input.txt', 'r') as file:
        total_operations = int(file.readline())

    zoo = {}

    with open('output.txt', 'w') as file:
        for _ in range(total_operations):
            operation = file.readline().split()

            if operation[0] == '+':

                animal = operation[1]
                if animal in zoo:
                    zoo[animal] += 1
                else:
                    zoo[animal] = 1

            elif operation[0] == '?':

                time = int(operation[1])
                count = 0

                for animal, feedings in zoo.items():
                    if 500 <= feedings <= time:
                        count += 1

                file.write(str(count) + '\n')
