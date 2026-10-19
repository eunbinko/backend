from pydantic import BaseModel, ConfigDict

#조회용 요청 X

#조회용 응답, 번호, 제목, 내용
class ReadRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    idx: int
    title: str
    contents: str

class BoardListRes(BaseModel):
    code: int
    message: str
    result: list[ReadRes]

class BoardRes(BaseModel):
    code: int
    message: str
    result: ReadRes

#작성용 요청, 제목, 내용
class RegisterReq(BaseModel):
    title: str
    contents: str
#작성용 응답, 번호, 제목, 내용
class RegisterRes(BaseModel):
    code: int
    message: str
    result: ReadRes
