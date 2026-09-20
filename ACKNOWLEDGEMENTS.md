# Acknowledgements

JevGraph builds on open-source work from the broader document intelligence and relation-extraction
communities.

## LlamaIndex DocJev

Document ingestion in JevGraph uses the optional
[`DocJev`](https://github.com/jerryjliu/docjev) package created by Jerry Liu and the LlamaIndex
community. JevGraph pins DocJev revision `9ed0fe05984ce1906af9272b8b400c8d46520f98` and uses its local
document-conversion path together with LiteParse metadata to preserve canonical pages and map graph
evidence back to source pages.

DocJev's hosted classification and document-splitting APIs are not part of the JevGraph ingestion
command. Results reproduced from DocJev are labeled as adjacent evidence rather than JevGraph
end-to-end measurements.

DocJev and LiteParse remain governed by their own licenses and attribution requirements. Thank you
to Jerry Liu, LlamaIndex, and their contributors for making this work available.

## FewRel

The public relation-selection experiments use FewRel from THUNLP. JevGraph does not redistribute
the dataset; the downloader pins an upstream revision and verifies its integrity. Users should
retain the upstream license and citation when publishing derived results.
