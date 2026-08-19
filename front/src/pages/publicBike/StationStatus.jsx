import { useEffect, useState } from "react";
import StationCard from "../../components/cards/StationCard";
import AreaChartCard from "../../components/charts/AreaChartCard";
import Loading from "../../components/common/Loading";
import publicBikeService from "../../services/publicBikeService";

// DemandForecast.jsx가 저장해두는, "마지막으로 선택한 대여소" 공유 key
const LAST_SELECTED_STATION_KEY = "pedalup_last_station_id";

const LEGEND = [
	{ label: "충분", color: "bg-neon" },
	{ label: "부족", color: "bg-warn" },
	{ label: "없음", color: "bg-danger" },
];

export default function StationStatus() {
	const [data, setData] = useState(null);
	const [baseStationId, setBaseStationId] = useState(null);

	useEffect(() => {
		// AI 수요예측에서 마지막으로 선택한 대여소 기준 조회
		const saved = localStorage.getItem(LAST_SELECTED_STATION_KEY);
		const stationId = saved ? Number(saved) : null;
		setBaseStationId(stationId);

		publicBikeService.getStations(stationId).then(setData);
	}, []);

	if (!data) return <Loading />;

	const baseStationName = data.stations.find(
		(s) => s.id === baseStationId,
	)?.name;

	return (
		<div>
			<div className="mb-6 flex flex-wrap items-center justify-between gap-4">
				<div>
					<p className="text-sm font-semibold text-bike">실시간 현황</p>
					<h2 className="mt-1 text-2xl font-extrabold text-white">
						{baseStationName ? `${baseStationName} 주변 대여소` : "대여소 현황"}
					</h2>
					{!baseStationId && (
						<p className="mt-1 text-xs text-gray-500">
							AI 예측 페이지에서 대여소를 먼저 선택하면, 그 대여소 기준으로
							보여드려요.
						</p>
					)}
				</div>
				<div className="flex items-center gap-4 text-xs text-gray-400">
					{LEGEND.map((item) => (
						<span key={item.label} className="flex items-center gap-1.5">
							<span className={`h-2 w-2 rounded-full ${item.color}`} />
							{item.label}
						</span>
					))}
				</div>
			</div>

			<div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{data.stations.map((station) => (
					<StationCard key={station.id} station={station} />
				))}
			</div>

			<p className="mb-1 text-sm font-semibold text-bike">시간대 분석</p>
			<h2 className="mb-4 text-2xl font-extrabold text-white">
				{baseStationName
					? `${baseStationName}의 오늘 시간대별 이용량`
					: "오늘의 시간대별 이용량"}
			</h2>
			<AreaChartCard
				data={data.hourlyUsage}
				xKey="hour"
				yKey="count"
				color="#38BDF8"
			/>
		</div>
	);
}
