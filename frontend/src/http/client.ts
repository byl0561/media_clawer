import axios from "axios";

/** Uniform result so callers never deal with thrown errors. */
export interface ApiResult<T> {
    success: boolean;
    data?: T;
}

const client = axios.create({timeout: 300000});

/** GET `url`, returning `{success:false}` instead of throwing on failure. */
export async function httpGet<T>(url: string): Promise<ApiResult<T>> {
    try {
        const res = await client.get<T>(url);
        return {success: true, data: res.data};
    } catch {
        return {success: false};
    }
}

/** POST `url` with a JSON `body`, same never-throws contract as httpGet. */
export async function httpPost<T>(
    url: string,
    body: unknown,
): Promise<ApiResult<T>> {
    try {
        const res = await client.post<T>(url, body);
        return {success: true, data: res.data};
    } catch {
        return {success: false};
    }
}

/**
 * Open an SSE stream to `url` and resolve when the server sends a `result`
 * event. Returns the same `ApiResult<T>` shape as `httpGet` so callers and
 * the `once()` memoisation helper need no changes.
 *
 * The server sends `: heartbeat` comments every ~10 s while computing, which
 * prevents proxy / browser timeouts without any client-side polling.
 */
export function httpGetSSE<T>(
    url: string,
    onProgress?: (step: string) => void,
): Promise<ApiResult<T>> {
    return new Promise((resolve) => {
        const es = new EventSource(url);
        let resolved = false;

        const done = (result: ApiResult<T>) => {
            if (!resolved) {
                resolved = true;
                es.close();
                resolve(result);
            }
        };

        es.addEventListener("progress", (e: MessageEvent) => {
            if (!onProgress) return;
            try {
                const d = JSON.parse((e as MessageEvent).data);
                if (d?.step) onProgress(d.step);
            } catch {}
        });

        es.addEventListener("result", (e: MessageEvent) => {
            try {
                done({success: true, data: JSON.parse(e.data) as T});
            } catch {
                done({success: false});
            }
        });

        es.addEventListener("error", (e: MessageEvent) => {
            // Custom "error" event from the server (upstream unavailable etc.)
            done({success: false});
        });

        es.onerror = () => {
            // Connection-level error (server unreachable, stream closed unexpectedly)
            done({success: false});
        };
    });
}
