"""
第4問（関数）
引数として width（幅）と height（高さ）を受け取り、長方形の面積を計算して戻り値として返す関数 get_area を定義してください。
"""
def get_area(width, height):
    return width * height

if __name__ == "__main__":
    print("長を入力してください")
    width = float(input())
    print("高さを入力してください")
    height = float(input())
    area = get_area(width, height)
    print(f"長方形の面積は {int(area)} です。")