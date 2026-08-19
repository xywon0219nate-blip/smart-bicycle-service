from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from core.deps import get_current_user
from models.member import UserModel

dashboard_router = APIRouter()


def _calc_joined_days(created_at: datetime) -> int:
   """가입일(created_at) 기준 '가입 N일째'를 계산.
   가입 당일이 1일째가 되도록 +1 처리.
   DB에서 읽어온 값이 naive datetime으로 올 수도 있어서(드라이버/컬럼 타입에 따라
   tzinfo가 날아가는 경우가 있음), 그 경우 UTC로 간주해서 맞춰준다.
   """
   if created_at.tzinfo is None:
      created_at = created_at.replace(tzinfo=timezone.utc)
   now = datetime.now(timezone.utc)
   return max(1, (now - created_at).days + 1)


@dashboard_router.get("/dashboard")
async def get_dashboard(currentUser: UserModel = Depends(get_current_user)) -> dict:
   return {
      "user": {
         "name": currentUser.nickname,
         "handle": "@" + currentUser.email.split("@")[0],
         "level": "입문 라이더",       # TODO: 실제 레벨 로직 생기면 교체
         "joinedDays": _calc_joined_days(currentUser.created_at),
         "streak": 0,                 # TODO: 라이딩 기록 테이블 생기면 연속 일수 계산으로 교체
      },
      "totals": [
         {"label": "총 라이딩", "value": "0", "unit": "회", "icon": "Map"},
         {"label": "누적 거리", "value": "0", "unit": "km", "icon": "TrendingUp"},
         {"label": "총 라이딩 시간", "value": "0", "unit": "h", "icon": "Clock"},
         {"label": "연속 라이딩", "value": "0", "unit": "일", "icon": "Flame"},
      ],
      "activity": {
         "badges": 0,
         "challenges": 0,
         "followers": 0,
         "savedRoutes": 0,
      },
      "recommendedRoute": None,
      "quickMenu": [
         {"icon": "Map", "label": "루트 탐색", "path": "/riding/start"},
         {"icon": "Bike", "label": "따릉이", "path": "/bike/seoul"},
         {"icon": "Users", "label": "커뮤니티", "path": "/community"},
         {"icon": "Trophy", "label": "챌린지", "path": "/challenges"},
      ],
      "communityFeed": [],
   }