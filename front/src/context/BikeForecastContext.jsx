import {
	createContext,
	useCallback,
	useContext,
	useMemo,
	useState,
} from "react";

// 대여소 현황(StationStatus) / AI 수요예측(DemandForecast) / 상단 요약 카드(BikeLayout)가
// 함께 보는 "마지막 예측 결과" 상태.
//
// localStorage 대신 React Context(메모리 상태)를 쓰는 이유:
// - 탭(대여소 현황 <-> AI 수요예측 등)을 옮겨도 BikeLayout이 언마운트되지 않으므로 값이 그대로 유지됨
//   -> 예전처럼 "경로가 바뀌면 지운다" 같은 별도 추적 로직이 필요 없음
// - 새로고침(F5)하면 이 상태는 자연스럽게 초기화됨 (JS가 다시 로드되므로)
// - 대여소 선택값(stationId)과 카드 요약(summary)을 하나의 객체로 묶어서 갱신하므로,
//   "카드만 남아있고 선택값은 사라짐" 같은 불일치가 생기지 않음
// - version은 "같은 대여소로 다시 예측"해도 대여소 현황이 최신값으로 재조회되도록 하기 위한 값
const BikeForecastContext = createContext(null);

export function BikeForecastProvider({ children }) {
	const [forecastResult, setForecastResultState] = useState(null);

	// DemandForecast가 예측을 실행할 때마다 대여소 id + 카드 요약 + 예측에 쓴 조건(params)을 한 번에 갱신.
	// params(date/hour/날씨)는 대여소 현황 탭이 "방금 실행한 예측과 같은 조건"으로 재조회할 때 씀.
	// 같은 대여소를 다시 예측해도 version이 올라가므로 대여소 현황 쪽 재조회 effect가 다시 실행됨.
	const setForecastResult = useCallback(({ stationId, summary, params }) => {
		setForecastResultState((prev) => ({
			stationId,
			summary,
			params,
			version: (prev?.version ?? 0) + 1,
		}));
	}, []);

	const value = useMemo(
		() => ({
			stationId: forecastResult?.stationId ?? null,
			forecastSummary: forecastResult?.summary ?? null,
			forecastParams: forecastResult?.params ?? null,
			forecastVersion: forecastResult?.version ?? 0,
			setForecastResult,
		}),
		[forecastResult, setForecastResult],
	);

	return (
		<BikeForecastContext.Provider value={value}>
			{children}
		</BikeForecastContext.Provider>
	);
}

export function useBikeForecast() {
	const ctx = useContext(BikeForecastContext);
	if (!ctx) {
		throw new Error(
			"useBikeForecast는 BikeForecastProvider 하위에서만 사용할 수 있어요.",
		);
	}
	return ctx;
}
