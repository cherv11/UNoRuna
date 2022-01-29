# 1. Прочитать (питоньей программой, конечно)) Анну Каренину, составить словарь частот букв, вывести топ-5 букв по популярности
from collections import Counter

text = open('karenina.txt', 'r', encoding='utf-8').read()
text = text.replace('\n', '').replace(' ', '')
words = list(text)
c = Counter(words)
print(c.most_common(5))

# 2. Написать функцию, которая на вход принимает натуральное число n, а возвращает словарь, в котором ключи - это числа от 1 до n,
# значения ключей - квадраты соответствующих чисел
def squaredict(n):
    d = {}
    for i in range(1, n+1):
        d[i] = i**2
    return d

print(squaredict(10))
# 3. С помощью map и лямбда функции из двух списков строк составить список содержащий на каждой позиции самую длинную строку
# из двух, что стоят в исходных списках на соответствующем месте
a = ['a', 'aaa', 'aaaa', 'dsd']
b = ['aa', 'aaaaa', 'aa']

print(list(map(lambda x: x[0] if len(x[0]) > len(x[1]) else x[1], zip(a,b))))



