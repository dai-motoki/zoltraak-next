# 掛け算を行う関数
def multiply(a: int, b: int) -> int:
    """
    2つの整数を受け取り、その積を返す関数です。

    :param a: 1つ目の整数
    :param b: 2つ目の整数
    :return: aとbの積
    """
    return a * b

# テスト用のコード
if __name__ == "__main__":
    # ユーザーから入力を受け取る
    num1 = int(input("1つ目の数字を入力してください: "))
    num2 = int(input("2つ目の数字を入力してください: "))

    # 掛け算を実行
    result = multiply(num1, num2)

    # 結果を表示
    print(f"{num1} × {num2} = {result}")

# 注意: このプログラムは簡単な掛け算を行うだけの基本的なものです。
# 実際のプロジェクトでは、より堅牢なエラーハンドリングや
# 入力値の検証を行うことをお勧めします。