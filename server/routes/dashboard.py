from fastapi import APIRouter, Depends

from core.deps import get_current_user
from models.member import UserModel

dashboard_router = APIRouter()


@dashboard_router.get("/dashboard")
async def get_dashboard(currentUser: UserModel = Depends(get_current_user)) -> dict:
   return {
      "user": {
         "name": currentUser.nickname,
         "handle": "@" + currentUser.email.split("@")[0],
         "level": "입문 라이더",       # TODO: 실제 레벨 로직 생기면 교체
         "joinedDays": 0,             # TODO: created_at 기준 계산
         "streak": 0,
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