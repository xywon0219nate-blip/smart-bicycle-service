import api from "../api/axios";
import {
	BIKE_HERO_STATS,
	STATIONS_MOCK,
	HOURLY_USAGE,
	MONTHLY_USAGE,
	TOP_STATIONS,
	AGE_DISTRIBUTION,
	AI_INSIGHTS,
	ROUTES_MOCK,
	FORECAST_STATIONS,
} from "../constants/mockData";

// 향후 FastAPI: GET /api/bike/seoul/summary
async function getSummary() {
	try {
		const { data } = await api.get("/bike/seoul/summary");
		return data;
	} catch {
		return BIKE_HERO_STATS;
	}
}

// 향후 FastAPI: GET /api/bike/seoul/routes
async function getBikeRoutes() {
	try {
		const { data } = await api.get("/bike/seoul/routes");
		return data;
	} catch {
		return ROUTES_MOCK.filter((r) => r.bikeType === "따릉이");
	}
}

// 향후 FastAPI: GET /api/bike/seoul/stations
// async function getStations() {
// 	try {
// 		const { data } = await api.get("/bike/seoul/stations");
// 		return data;
// 	} catch {
// 		return { stations: STATIONS_MOCK, hourlyUsage: HOURLY_USAGE };
// 	}
// }

async function getStations(stationId, forecastParams) {
	const { data } = await api.get("/bike/seoul/stations", {
		params: {
			...(stationId ? { station_id: stationId } : {}),
			...(forecastParams?.date ? { date: forecastParams.date } : {}),
			...(forecastParams?.hour !== undefined && forecastParams?.hour !== null
				? { hour: forecastParams.hour }
				: {}),
			...(forecastParams?.temperature !== undefined
				? { temperature: forecastParams.temperature }
				: {}),
			...(forecastParams?.humidity !== undefined
				? { humidity: forecastParams.humidity }
				: {}),
			...(forecastParams?.rainfall !== undefined
				? { rainfall: forecastParams.rainfall }
				: {}),
			...(forecastParams?.windSpeed !== undefined
				? { wind_speed: forecastParams.windSpeed }
				: {}),
		},
	});
	return data;
}

// 향후 FastAPI: GET /api/ai/bike/analysis
// year/month를 안 넘기면 서버가 데이터상 가장 최근 달 기준으로 응답함
async function getAnalysis({ year, month } = {}) {
	try {
		const { data } = await api.get("/ai/bike/analysis", {
			params: year && month ? { year, month } : {},
		});
		return data;
	} catch {
		return {
			monthlyUsage: MONTHLY_USAGE,
			topStations: TOP_STATIONS,
			ageDistribution: AGE_DISTRIBUTION,
			insights: AI_INSIGHTS,
		};
	}
}

// ===== 수정 시작: 실제 백엔드(/api/ai/bike/forecast)에 맞게 요청/응답 형태 전체 교체 =====
// 기존에는 station_id, recent_1h_rental_count 등 "대여소별 + 과거 대여량" 기반 요청을 보내고,
// 실패하면 mockForecast()로 대체했음.
// 이 함수(getForecast)는 2017~2018년 UCI 공개 데이터로 학습한 "서울시 전체" 단위 모델
// (bike_demand_model.pkl)을 호출한다. 지금은 DemandForecast.jsx에서 더 이상 쓰지 않지만
// (아래 getStationForecast로 대체됨), 나중에 "서울시 전체 예측" 화면이 따로 필요해지면
// 재사용할 수 있어서 남겨둔다.
async function getForecast({
	hour,
	temperature,
	humidity,
	windSpeed,
	visibility,
	dewPoint,
	solarRadiation,
	rainfall,
	snowfall,
	season,
	holiday,
	functioningDay,
}) {
	const { data } = await api.post("/ai/bike/forecast", {
		hour,
		temperature,
		humidity,
		wind_speed: windSpeed,
		visibility,
		dew_point: dewPoint,
		solar_radiation: solarRadiation,
		rainfall,
		snowfall,
		season,
		holiday,
		functioning_day: functioningDay,
	});
	return data;
}

// 향후 FastAPI: GET /api/ai/bike/districts — 대여소 검색용 구(區) 목록
async function getForecastDistricts() {
	const { data } = await api.get("/ai/bike/districts");
	return data;
}

// 향후 FastAPI: GET /api/ai/bike/stations — 실제 대여소 목록(station_master.csv 기반)
async function getForecastStations(district) {
	const { data } = await api.get("/ai/bike/stations", {
		params: district ? { district, limit: 200 } : { limit: 200 },
	});
	return data;
}

// 향후 FastAPI: POST /api/ai/bike/station-forecast
// station_demand_model(대여소 패턴) x weather_effect_model(날씨 배율)을 조합한 대여소별 예측
async function getStationForecast({
	stationId,
	date,
	hour,
	temperature,
	humidity,
	rainfall,
	windSpeed,
}) {
	const { data } = await api.post("/ai/bike/station-forecast", {
		station_id: stationId,
		date,
		hour,
		temperature,
		humidity,
		rainfall,
		wind_speed: windSpeed,
	});
	return data;
}

const publicBikeService = {
	getSummary,
	getBikeRoutes,
	getStations,
	getAnalysis,
	getForecast,
	getForecastDistricts,
	getForecastStations,
	getStationForecast,
};
export default publicBikeService;
