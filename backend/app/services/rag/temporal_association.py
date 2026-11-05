
def associate_temporal_evidence(
    transcript_segments: list[dict],
    visual_frames: list[dict],
    window_seconds: float = 5.0,
    max_frames: int = 3,
) -> list[dict]:
    """
    Associate transcript segments with nearby visual frames.

    A frame is associated when its timestamp is within the
    configured temporal window of a transcript segment.
    """

    if window_seconds < 0:
        raise ValueError("Window must be non-negative.")

    if isinstance(max_frames, bool) or not isinstance(max_frames, int) or max_frames < 1:
        raise ValueError("max_frames must be a positive integer.")

    associated_segments = []

    for segment in transcript_segments:
        segment_start = segment["start_seconds"]
        segment_end = segment["end_seconds"]

        if segment_start > segment_end:
            raise ValueError("Transcript start cannot exceed end.")

        nearby_frames = []

        for frame in visual_frames:
            if frame["video_id"] != segment["video_id"]:
                continue

            frame_time = frame["start_seconds"]

            if frame_time < segment_start:
                gap = segment_start - frame_time
            elif frame_time > segment_end:
                gap = frame_time - segment_end
            else:
                gap = 0.0

            if gap <= window_seconds:
                nearby_frames.append({
                    "evidence_id": frame["evidence_id"],
                    "video_id": frame["video_id"],
                    "timestamp": frame["timestamp"],
                    "timestamp_seconds": frame["start_seconds"],
                    "text": frame["text"],
                    "temporal_gap_seconds": round(gap, 3),
                })

        nearby_frames.sort(
            key=lambda frame: frame["temporal_gap_seconds"]
        )

        associated_segment = segment.copy()
        associated_segment["associated_visual_evidence"] = (
            nearby_frames[:max_frames]
        )

        associated_segments.append(associated_segment)

    return associated_segments
