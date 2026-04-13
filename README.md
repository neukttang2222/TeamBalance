# Team Balance

텍스트 제출물 기반 AI 기여도 판단 웹 서비스 입니다.

## 소개
이 프로젝트는 사용자가 부여된 태스크에 대한 결과를 제출하면, 질문 규칙에 맞춰 AI가 역질문을 생성합니다.
AI는 역질문에 대한 작성자의 답변을 통해, 제출물에 대한 이해정도를 평가하여 점수를 측정합니다.
측정된 점수를 기반으로 각 팀원들의 기여도를 비교하고, 시각화합니다.

## 실행 방법
https://team-balance-xi.vercel.app/ 링크에 접속하면 사용이 가능합니다.

## 주의 사항
이 웹 서비스는 Vercel 과 Render 의 무료 플랜을 사용하여 배포를 하였습니다.
Render 무료 플랜을 사용하여, 첫 동작 시, 약 1분 정도의 시간이 소요될 수 있으나,
첫 동작 이후부터는, 원활하게 사용하실 수 있습니다.

AI 는 Gemini api 무료 티어, Gemini 2.5 Flash Lite 모델을 사용하여 구현하였습니다.
사용량에 제한에 걸리면, Answer 단계에서, AI 채점에 실패했다는 Failed 상태를 받을 수 있습니다.
해당 상황에서는 시간을 두고 retry 시도를 해주시면 감사하겠습니다. 

## 사용 방법
1. 로그인
<img width="972" height="751" alt="image" src="https://github.com/user-attachments/assets/d485f54d-95d3-41e8-b986-b507922f4b17" />

등록한 이메일과, 비밀번호를 입력하고, 로그인 버튼을 누르면 첫화면으로 넘어갈 수 있습니다.
등록한 이메일이 없다면, 회원가입을 통해 생성할 수 있습니다.

2. 회원가입
<img width="906" height="946" alt="image" src="https://github.com/user-attachments/assets/facaf4dc-5b39-423e-994d-b14905f593f3" />

프로젝트에서 사용할 이름, 아이디로 사용할 이메일, 비밀번호를 입력한 뒤, 회원가입 버튼을 누르면,
계정을 생성하실 수 있습니다.

3. 프로젝트의 첫 화면 (Project Entry)
<img width="1243" height="799" alt="image" src="https://github.com/user-attachments/assets/19024d3a-85fc-4967-8c2f-c3399ff94198" />

상단의 Project Entry , Task Workspace, Project Dashboard 버튼을 통해 각 페이지로 이동할 수 있습니다.

Project Entry 에서는 팀 생성 및 편집, 프로젝트 생성 및 편집을 하실 수 있습니다.
생성은 + 버튼을 통해, 편집은 생성된 팀과 프로젝트 옆의 edit 버튼을 통해 하실 수 있습니다.
edit 는 member 역할의 유저는 표시되지않으니, 참고하시면 좋을 것 같습니다.

4. 팀 생성 및 편집 화면
<img width="997" height="803" alt="image" src="https://github.com/user-attachments/assets/1d8195de-43ed-4ca7-ac86-ffdb623b0101" />
<img width="1004" height="1214" alt="image" src="https://github.com/user-attachments/assets/1d312c06-fa9d-4000-aab1-dab868d2ce1a" />

생성 화면과 편집 화면의 구성은 동일합니다. 
team name 과, 팀원을 멤버 검색 기능을 통해 선택하고, 생성 버튼, 저장 버튼을 누르면 팀 생성 작업 및 수정 작업이 가능합니다.
팀원을 추가한 후에는 role 을 설정할 수 있고, x 버튼을 통해, 삭제할 수 있습니다.

5. 프로젝트 생성 및 편집 화면
<img width="999" height="1232" alt="image" src="https://github.com/user-attachments/assets/d46dfa0e-77d5-48a1-8941-73ccc785d06e" />
<img width="999" height="1218" alt="image" src="https://github.com/user-attachments/assets/c80dd767-822c-4011-bd4b-aa17eba52027" />

프로젝트도 생성 화면과 편집 화면 구성이 동일합니다.
project name, 소속 팀, project goal, 프로젝트 멤버를 선택 및 수정 후, 아래 생성, 저장 버튼을 누르면,
프로젝트 생성, 수정 작업을 하실 수 있습니다.
팀 화면과 마찬가지로, role 을 선택할 수 있고, x 버튼을 통해, 삭제할 수 있습니다.

이후 생성된 프로젝트를 선택하면 Task 작업 화면으로 넘어가실 수 있습니다.

6. Task 작업 화면
<img width="1177" height="1243" alt="image" src="https://github.com/user-attachments/assets/33554454-972d-4888-afea-ab961148b9f0" />

해당 화면에서는 Task 생성과 작업을 할 수 있습니다.

<img width="667" height="892" alt="image" src="https://github.com/user-attachments/assets/45e4154c-5531-4584-a2ab-68269e6328d1" />

task 생성 화면입니다.
task 생성은 일반 member 는 사용하실 수 없습니다.
task 주제, type, 목표를 설정하시고, 담당자를 선택하시면 task 생성을 하실 수 있습니다.
Task의 난이도에 따라 weight 를 설정하여, 추가 점수를 부여할 수 있습니다.
생성된 task 는 왼쪽 아래의 task list에서 확인할 수 있습니다.

<img width="947" height="926" alt="image" src="https://github.com/user-attachments/assets/33fc6dec-cd2b-44fe-87ec-20b5c2c96f5a" />

task 편집 화면입니다.
task 생성과 동일한 구성으로 되어있고, 일반 member 는 역시 접근할 수 없습니다.

<img width="802" height="778" alt="image" src="https://github.com/user-attachments/assets/d4c599c5-769a-4f69-9d87-c288a63632bd" />

task 제출 화면으로, 정리하거나 조사한 텍스트 결과물을 제출하시면 됩니다.

<img width="780" height="780" alt="image" src="https://github.com/user-attachments/assets/09cc83ea-84e8-4ba8-b6a5-0ccf36996e88" />

이후 제출물에 대한 AI 역질문을 받고, 답변을 입력하시면 되겠습니다.

<img width="782" height="858" alt="image" src="https://github.com/user-attachments/assets/679bc226-8279-4801-9737-19f564a7723f" />

이렇게 평가가 결정이 되고, manager 나 owner 역할의 권한을 가진 사용자가, 위의 [작업 보기] 에서 검토 뷰를 선택하여,
승인 또는 보완, 추가점수 부여 등을 선택하여 점수를 확정지어 주거나, 미흡한 부분 추가 요청을 하실 수 있습니다.

승인을 받으면 최종 점수가 작업자의 개인 뷰 (작업 보기 -> 내 작업)에 추가되어 보입니다.

7. 프로젝트 대시보드 화면
<img width="1144" height="1219" alt="image" src="https://github.com/user-attachments/assets/882194d7-77d5-4316-9cb1-1f2ef8e1bfd2" />


선택한 프로젝트의 사용자별 task 완료 정보가 나옵니다.
각 사용자의 누적 점수를 원 그래프로 시각화하여 한눈에 볼 수 있습니다.


 
