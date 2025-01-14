import pandas as pd
import re
# from pykospacing import Spacing
# from hanspell import spell_checker

path = "/opt/ml/input/final-project-level3-nlp-07/data/hate_data.csv"                                                # 파일의 폴더 경로
# output_path = "경로 입력 필요"

# df = pd.read_csv(path + "파일 이름")                         # csv 파일 DataFrame으로 불러오기
hate_df = pd.read_csv(path)
hate = sorted(hate_df["hate"], key=len, reverse=True)

# df = df[1:]                                                     # 내보내기 후 첫 대화는 카카오톡 안내사항


def id_check(my_id):                                            # 방장 봇이면 False, 일반 유저인 경우 True
    if my_id == "방장봇":
        return False

    return True

def text_processing(dialog):                                    # Text 전처리 작업
    find_text = re.findall('[ㄱ-ㅎㅏ-ㅣ]+', dialog)
    vowel = "".join(find_text)

    if vowel == dialog:
        return False

    if len(dialog) == 0:
        return False

    if dialog == "삭제된 메시지입니다." or dialog == "채팅방 관리자가 메시지를 가렸습니다.":
        return False

    if "님이 나갔습니다." == dialog[-9:] or "님이 들어왔습니다." == dialog[-10:] or "저장한 날짜 : " in dialog:
        return False

    if dialog == "이모티콘" or dialog == "사진" or dialog == "카카오톡 프로필" or dialog == "음성메시지" or dialog == "보이스룸이 방금 시작했어요." or \
    dialog[:7] == "보이스룸 종료" or dialog[:7] == "라이브톡 종료" or dialog[:7] == "라이브톡 시작":
        return False

    return True

def text_replace(dialog):                                       # '\n' -> ' ' , 링크 -> [LINK] 로 변경

    dialog = dialog.replace("\r", " ")
    dialog = dialog.replace("\n", " ")

    web = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    dialog = re.sub(pattern=web, repl ="[LINK]", string=dialog)

    # emoji_pattern = re.compile("["u"\U00010000-\U0010FFFF""]+", flags=re.UNICODE)         # 유니코드 기준 이모티콘 제거
    # dialog = emoji_pattern.sub(r'', dialog)

    dialog = " ".join(dialog.split())                           # 다중 공백 -> 한개의 공백

    return dialog.strip()

def useless(dialog):                                             # min_length 이상 max_length 이하 데이터는 True, 아니면 False
    min_length = 5
    max_length = 1000
    if len(dialog) < min_length:
        return False

    elif len(dialog) > max_length:
        return False

    return True

def hate_replace(dialog):                                        # 혐오발언 및 욕설 "*"으로 치환

    for i in hate:
        if i in dialog:
            dialog = dialog.replace(i, '*'*len(i))
            dialog = " ".join(dialog.split())

    return dialog.strip()

def same(df):                                                   # 한 사람이 주요 정보를 여러개 발화로 할 경우 → 한 문장으로 보기
    before_id = ""
    idx = -1

    for index, row in df.iterrows():
        if before_id == row["User"]:
            df.loc[index, "same_id"] = False
            df.loc[idx, "Message"] += " " + df.loc[index, "Message"]

        else:
            before_id = row["User"]
            idx = index

    df = df[df["same_id"] == True][["index","Date", "User", "Message"]].reset_index(drop=True)

    return df

# def pyko(dialog):                                             # 맞춤법 확인 후 띄어쓰기

#     dialog = spell_checker.check(dialog)
#     dialog = dialog.checked

#     dialog = "".join(dialog.split())
#     dialog = spacing(dialog)

#     return dialog

"""
    Date = 메시지 보낸 시간
    User = 이름
    Message = 메시지
"""

def _preprocess(new_df):
    df = new_df.copy()
    df["id_boolean"] = df["User"].apply(id_check)                   # 방장봇이 대화하면 제거
    df["Message"] = df["Message"].apply(text_replace)               # \n, 링크 전처리 작업
    df["Message"] = df["Message"].apply(hate_replace)
    df["text_boolean"] = df["Message"].apply(text_processing)       # 제거 목록 전처리 작업

    df = df[(df["id_boolean"] == True) & (df["text_boolean"] == True)][["index","Date", "User", "Message"]]     # 전처리 작업 후 (True & True) Data 사용

    df["same_id"] = True
    df = same(df)

    df["length"] = df["Message"].apply(useless)                     # 데이터 길이가 min_length 이상 max_length 이하 데이터만 사용
    df['Message2'] = pd.concat([df['Message'].iloc[1:],pd.Series('None')]).reset_index(drop=True)
    df = df[df["length"] == True][["index","Date", "User", "Message","Message2"]].reset_index(drop=True)       # 모든 작업이 완료된 DataFrame

    # df["Message"] = df["Message"].apply(pyko)

    return df

# df.to_csv(output_path + "train.csv", index=False)


