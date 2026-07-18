"""
第5問（クラスの基本と初期化）
Student という名前のクラスを定義してください。また、インスタンス化されるときに student_id（学籍番号）と name（名前）を受け取ってインスタンス変数に格納する、初期化メソッド（__init__）を記述してください。

第6問（クラスのメソッド）
第5問で作成した Student クラスに、自身の学籍番号と名前を「学籍番号:〇〇, 名前:△△」の形式で画面に出力するメソッド print_info(self) を追加してください。

第7問（インスタンスの生成と実行）
第6問の Student クラスから、学籍番号が 1234、名前が "鈴木太郎" のインスタンス student_a を作成し、print_info メソッドを呼び出すコードを書いてください。
"""
class Student:
    def __init__(self, student_id, name):
        self.student_id = student_id
        self.name = name
    @classmethod
    def create_student(cls, student_id_name):
        id=student_id_name.split("-")[0]
        name=student_id_name.split("-")[1]
        return cls(id, name)
    @staticmethod
    def print_info(self):
        print(f"学籍番号:{self.student_id}, 名前:{self.name}")
if __name__ == "__main__":
    temp_student = Student("55688", "namae")
    temp_student.print_info(temp_student)
    print("学籍番号と名前を入力してください（例：12345-NAME）")
    student_id_name = input()
    student = Student.create_student(student_id_name)
    student.print_info(student)