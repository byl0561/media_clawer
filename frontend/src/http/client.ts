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
