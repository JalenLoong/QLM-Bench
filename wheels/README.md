# Reviewed CPU core artifact

qlm_bench-0.1.0-py3-none-any.whl is the reviewed159804-byte standalone CPU core.
SHA256:7efc271a40a16c39fc28b53c5acacb448310a2a7491f2f1ec64020693ace6fc8.
Its package modules/specs equal the accepted source and it contains no simulator,
controller/model weights or large asset payloads. WAM v2/v3 requirement locks consume
this exact archive. From this QLM checkout, install with --no-index --find-links ./wheels
and the consumer's --require-hashes lock; optional CPU data dependencies are separate.
