import { useCallback, useEffect, useMemo, useState } from "react";
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

    const queryKey = useMemo(() => {
        if (!query) return "";
        return JSON.stringify(query);
    }, [query]);

    const reload = useCallback(() => {
        setReloadToken((prev) => prev + 1);
    }, []);

    useEffect(() => {
        if (!query) return;
        let canceled = false;

        setState((prev) => ({ ...prev, loading: true, error: null }));

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
                    error: err instanceof Error ? err.message : "Failed to load visual space",
                });
            });

        return () => {
            canceled = true;
        };
    }, [queryKey, reloadToken]);

    return { ...state, reload };
}
