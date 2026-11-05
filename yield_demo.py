# 首先定义一个使用了yield关键字的方法
def get_num_list():
    print("方法被调用了")
    num_list = []
    for i in range(10):
        num_list.append(i)
        yield num_list


if __name__ == '__main__':
    for result in get_num_list():
        print(result)

    print("-----------------------------------")

    result2 = get_num_list()
    print(next(result2))
    print("暂停一次")
    print(next(result2))

print(range(5))