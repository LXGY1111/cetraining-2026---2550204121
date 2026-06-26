def calc_average(num_list):
    """计算数字列表平均值"""
    if len(num_list) == 0:
        return 0
    total = sum(num_list)
    return total / len(num_list)

# 测试
if __name__ == "__main__":
    data = [10,20,30,40]
    print("平均值：", calc_average(data))