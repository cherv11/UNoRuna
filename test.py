def get_one(x, ops=0, order=''):
    if x == 0:
        return -1, ''
    if x == 1:
        return ops, order
    if x == 2:
        print(x, ops+1, order+'2')
        return ops+1, order+'2'
    opses = []
    orders = []
    if len(str(x)) % 2 == 0:
        half = len(str(x))//2
        one, two = int(str(x)[:half]), int(str(x)[half:])
        oneops, oneorder = get_one(one, ops+1, order+'3')
        twoops, twoorder = get_one(two, ops+1, order+'4')
        if oneops > -1:
            opses.append(oneops)
            orders.append(oneorder)
        if twoops > -1:
            opses.append(twoops)
            orders.append(twoorder)

        one, two = int(str(x)[:half]*2), int(str(x)[half:]*2)
        if not one == two:
            oneops, oneorder = get_one(one, ops+1, order+'5')
            twoops, twoorder = get_one(two, ops+1, order+'6')
            if oneops > -1:
                opses.append(oneops)
                orders.append(oneorder)
            if twoops > -1:
                opses.append(twoops)
                orders.append(twoorder)
    if x % 2 == 0 and (not order or order[-1] != '1'):
        oneops, oneorder = get_one(x//2, ops+1, order+'2')
        if oneops > -1:
            opses.append(oneops)
            orders.append(oneorder)
    if not opses:
        oneops, oneorder = get_one(x*2, ops+1, order+'1')
        if oneops > -1:
            opses.append(oneops)
            orders.append(oneorder)
    opses = [i for i in opses if i > -1]
    if opses:
        minops = min(opses)
        minorders = orders[opses.index(minops)]
        print(x, minops, minorders)
        return minops, minorders
    return -1, ''


for i in range(1):
    print(f'\033[33m{i}\033[0m')
    [print(x) for x in get_one(i)]

for i in range(100):
    print(f'\033[3{i%7}m{i}\033[0m')
