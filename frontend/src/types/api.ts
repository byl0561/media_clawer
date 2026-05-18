/** Server response shapes for the `/api/v1` endpoints. */

export interface MediaItemDTO {
    title: string;
    score: number | null;
    votes: number | null;
    poster: string | null;
    link: string | null;
}

export interface MovieItem extends MediaItemDTO {
    year: number;
}

export interface ShowItem extends MediaItemDTO {
    year: number[];
}

export interface AlbumItem extends MediaItemDTO {
    artist: string;
    year: number;
}

export interface BookItem extends MediaItemDTO {
    author: string;
}

export interface Diff<T> {
    missing: T[];
    extra: T[];
}

export interface CollectionGap {
    collection: string;
    missing: MovieItem[];
}

export interface SeasonRef {
    num: number;
    name: string;
}

export interface IncompleteSeason {
    season_num: number;
    season_name: string;
    local_max_episode: number;
    remote_max_episode: number;
}

export interface LocalGap {
    show: ShowItem;
    missing_seasons: SeasonRef[];
    incomplete_seasons: IncompleteSeason[];
}
