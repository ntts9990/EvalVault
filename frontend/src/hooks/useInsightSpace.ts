import { useCallback, useEffect, useState } from "react";
import {
    fetchVisualSpace,
    type VisualSpaceQuery,
    type VisualSpaceResponse,
} from "../services/api";

type InsightSpaceState = {
    data: VisualSpaceResponse | null;
    loading: boolean;
    error: string | null;
};

export function useInsightSpace(query: VisualSpaceQuery | null) {
    const [state, setState] = useState<InsightSpaceState>({
        data: null,
        loading: false,
        error: null,
    });
    const [reloadToken, setReloadToken] = useState(0);

    const reload = useCallback(() => {
        setReloadToken((prev) => prev + 1);
    }, []);

    useEffect(() => {
        if (!query) return;
        let canceled = false;

        Promise.resolve().then(() => {
            if (canceled) return;
            setState((prev) => ({ ...prev, loading: true, error: null }));
        });

        fetchVisualSpace(query.runId, {
            granularity: query.granularity,
            baseRunId: query.baseRunId,
            autoBase: query.autoBase,
            include: query.include,
            limit: query.limit,
            offset: query.offset,
            clusterMap: query.clusterMap,
        })
            .then((data) => {
                if (canceled) return;
                setState({ data, loading: false, error: null });
            })
            .catch((err: unknown) => {
                if (canceled) return;
                setState({
                    data: null,
                    loading: false,
                    error: err instanceof Error ? err.message : "시각화 데이터를 불러오지 못했습니다",
                });
            });

        return () => {
            canceled = true;
        };
    }, [query, reloadToken]);

    return { ...state, reload };
}
