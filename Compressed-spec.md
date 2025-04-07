# CodeQuilt v0.7.1-semantic-py3.11-std25-v1: LLM Encoder/Decoder Context (Complete Data)

**Goal:** Highly compressed Python 3.11 text representation for LLMs. Min tokens via fixed chars, implied corpus (C), dynamic dict (D), extended literals (X), semantic patterns (S). This IS the spec & data.

**Format:** `[Header]|||Body`

**Header (`[...]`):** `;`-sep Key:Value. Keys: `V,L,D,I,O,C,X`. Case-sens. No extra space.
* `V:0.7.1-semantic-py3.11-std25-v1` (REQUIRED/FIXED). Implies Corpus C & Fixed Tokens below.
* `L:python-3.11` (Optional, implied).
* `D:[d<n>=id,...]` (Dynamic): REQUIRED for non-C IDs. Start `d0`. `d<n>` in body maps here. Empty: `D:[]` or omit. `id`: `(letter | "_") (letter | digit | "_")*`.
* `X:[l<n>=b64,...]` (Extended Lits): REQUIRED if lit > `lth`, multiline, or comment (if `cmt=k`). Start `l0`. `b64`: Std Base64 of UTF-8 bytes. `l<n>` in body maps here.
* `I:[path1,path2 as alias,...]` (Imports): Optional info. `path`/`alias`: `safe-hdr-char+` (`a-zA-Z0-9_./+:-=`).
* `O:[opt1,opt2=val,...]` (Options): Optional. Defined: `cmt=k` (keep comments via X:/l<n>), `lth=N` (inline str/bytes max len, default 80). `val`: `safe-hdr-char+`.
* `C:<algo>-<hash>`: Optional checksum (e.g., `sha256-a1b...`). `algo`: id, `hash`: hex.

**Body (`...` after `|||`):** Token sequence. Whitespace chars BETWEEN tokens ignored.

**Body Tokens:**
* **Structure:** `N`(newline), `>`(indent+1), `<`(dedent-1), `( ) [ ] { } , : . ;`
* **Fixed Tok (See Map Below):** `D C R ... + - * ... t f n` etc.
* **Refs:** `c<n>`(Corpus C idx n), `d<n>`(Header D idx n), `l<n>`(Header X idx n, b64-decoded).
* **Inline Lits:** `123`, `-10`, `3.14`, `t`, `f`, `n`, `'abc'`, `"d'ef"`, `b'xy'`, `b"\\x01"`. Str/bytes MUST be <= `lth` & single-line. Escapes: `\\ \' \" \n \t \r \b \f \uXXXX`.
* **Semantic Tok (See Defs Below):** `LOG(...)`, `ATTR(...)`, etc. Uppercase name, `(` params `)` or `(` params `:` `{` body `}` `)`. Params sep by `:`.
* **Decorator:** `@` (prefix, followed by ref/fixed).
* **Escape:** `L'{raw_code}'`. Raw escapes: `\\ -> \\\\`, `} -> \\}`, `{ -> \\{`. Last resort.

---
**Corpus C (for V:0.7.1-semantic-py3.11-std25-v1; `c<n>` maps to entry `n`)**
`c0=Exception` `c1=AttributeError` `c2=IndexError` `c3=KeyError` `c4=ValueError` `c5=TypeError` `c6=ImportError` `c7=ModuleNotFoundError` `c8=FileNotFoundError` `c9=NotImplementedError` `c10=RuntimeError` `c11=OSError` `c12=sqlite3` `c13=JSONDecodeError` `c14=StopIteration` `c15=BaseException` `c16=LookupError` `c17=AssertionError` `c18=UnicodeError` `c19=UnicodeDecodeError` `c20=ConnectionError` `c21=TimeoutError` `c22=PermissionError` `c23=ReferenceError` `c24=SyntaxError` `c25=IndentationError` `c26=SystemError` `c27=RecursionError` `c28=return` `c29=import` `c30=except` `c31=finally` `c32=lambda` `c33=assert` `c34=global` `c35=yield` `c36=async` `c37=await` `c38=class` `c39=continue` `c40=isinstance` `c41=getattr` `c42=setattr` `c43=hasattr` `c44=enumerate` `c45=filter` `c46=sorted` `c47=property` `c48=classmethod` `c49=staticmethod` `c50=__init__` `c51=__repr__` `c52=__str__` `c53=__call__` `c54=__getitem__` `c55=__setitem__` `c56=__delitem__` `c57=__contains__` `c58=__enter__` `c59=__exit__` `c60=__iter__` `c61=__next__` `c62=append` `c63=extend` `c64=insert` `c65=remove` `c66=reverse` `c67=update` `c68=values` `c69=items` `c70=popitem` `c71=setdefault` `c72=discard` `c73=startswith` `c74=endswith` `c75=replace` `c76=strip` `c77=split` `c78=join` `c79=format` `c80=encode` `c81=decode` `c82=streamlit` `c83=session_state` `c84=sidebar` `c85=button` `c86=text_input` `c87=text_area` `c88=slider` `c89=selectbox` `c90=toggle` `c91=expander` `c92=markdown` `c93=caption` `c94=warning` `c95=success` `c96=toast` `c97=spinner` `c98=rerun` `c99=chat_message` `c100=chat_input` `c101=columns` `c102=container` `c103=set_page_config` `c104=logging` `c105=logger` `c106=getLogger` `c107=basicConfig` `c108=FileHandler` `c109=StreamHandler` `c110=setLevel` `c111=datetime` `c112=timedelta` `c113=fromisoformat` `c114=strftime` `c115=pathlib` `c116=resolve` `c117=exists` `c118=is_file` `c119=is_dir` `c120=read_text` `c121=mkdir` `c122=connect` `c123=cursor` `c124=execute` `c125=fetchone` `c126=fetchall` `c127=commit` `c128=rollback` `c129=lastrowid` `c130=rowcount` `c131=contextlib` `c132=contextmanager` `c133=loads` `c134=dumps` `c135=google` `c136=generativeai` `c137=configure` `c138=list_models` `c139=get_model` `c140=GenerativeModel` `c141=GenerationConfig` `c142=generate_content` `c143=start_chat` `c144=send_message` `c145=count_tokens` `c146=safety_settings` `c147=candidates` `c148=prompt_feedback` `c149=block_reason` `c150=citation_metadata` `c151=citation_sources` `c152=grounding_metadata` `c153=web_search_results` `c154=search_entry_point` `c155=rendered_content` `c156=GoogleSearchRetrieval` `c157=dynamic_retrieval_config` `c158=dynamic_threshold` `c159=disable_attribution` `c160=database` `c161=manager` `c162=context_manager` `c163=actions` `c164=requests` `c165=response` `c166=session` `c167=collections` `c168=defaultdict` `c169=OrderedDict` `c170=Counter` `c171=deque` `c172=namedtuple` `c173=argparse` `c174=ArgumentParser` `c175=add_argument` `c176=parse_args` `c177=subprocess` `c178=communicate` `c179=unittest` `c180=TestCase` `c181=assertEqual` `c182=assertTrue` `c183=assertFalse` `c184=assertRaises` `c185=threading` `c186=Thread` `c187=Condition` `c188=Semaphore` `c189=multiprocessing` `c190=Process` `c191=Queue` `c192=Pool` `c193=shutil` `c194=copy` `c195=move` `c196=rmtree` `c197=pickle` `c198=struct` `c199=socket` `c200=asyncio` `c201=gather` `c202=create_task` `c203=run_until_complete` `c204=sleep` `c205=wait` `c206=warnings` `c207=warn` `c208=simplefilter` `c209=traceback` `c210=format_exc` `c211=print_exc` `c212=inspect` `c213=getmembers` `c214=signature` `c215=Parameter` `c216=functools` `c217=partial` `c218=lru_cache` `c219=wraps` `c220=operator` `c221=itemgetter` `c222=attrgetter` `c223=methodcaller` `c224=tempfile` `c225=NamedTemporaryFile` `c226=TemporaryDirectory` `c227=itertools` `c228=product` `c229=permutations` `c230=combinations` `c231=chain` `c232=message` `c233=content` `c234=conversation` `c235=metadata` `c236=timestamp` `c237=instruction` `c238=parameter` `c239=context` `c240=history` `c241=variable` `c242=argument` `c243=function` `c244=module` `c245=package` `c246=default` `c247=result` `c248=status` `c249=client` `c250=server` `c251=request`

---
**Fixed Tokens (Implied by V)**
* **Struct:** `N > < ( ) [ ] { } , : . ;`
* **Ops:** `= + - * / % & | ^ ~ < > ! @` (`&`:and, `|`:or, `^`:xor/pow, `~`:is, `!`:not, `@`:in)
* **Kw:** `D` def, `C` class, `R` return, `?` if, `T` try, `X` except, `Y` finally, `P` pass, `M` import, `J` from, `E` elif, `B` break, `K` continue, `Q` del, `A` await, `S` async, `U` raise, `Z` assert, `W` with, `G` global, `L` lambda
* **Lit:** `t` True, `f` False, `n` None
* **Note:** Multi-char ops (`==`, `!=`, `+=`, etc) are sequences (e.g., `! =`, `+ =`). Use corpus refs for keywords if needed (e.g., `c28`=return).

---
**Semantic Tokens (S) Definitions & Expansions**
*(Assume c105=logger, c0=Exception, t=True, n=None for expansions)*
* `LOG(<lvl>:<fmt>[:<args...>])` -> `c105.<lvl>(<fmt>, *<args>)` [`<lvl>`: `i` info, `d` debug, `e` error, `w` warning, `c` critical (fixed tokens)]
* `TRYLOG(<err>:<var> {<body>})` -> `T : N > <body> N < X <err> as <var> : N > c105.e(f"FAIL: {<var>}", exc_info=t) N <`
* `RETN(<var>)` -> `? <var> ~ n : N > R n N <`
* `RETF(<var>)` -> `? ! <var> : N > R n N <`
* `RAISE(<chk>:<var>:<err>[:<args...>])` -> `? <check> : N > U <err>(*<args>) N <` [`<chk>`: `N` (`<var>~n`), `E` (`!<var>`) (fixed tokens)]
* `ATTR(<obj>:<attr>:<val>)` -> `<obj> . <attr> = <val>`
* `DGET(<tgt>:<dct>:<key>:<def>)` -> `<tgt> = <dct> . get ( <key> , <def> )`
* `DBEXEC(<sql>[:<params>])` -> `W c122() as conn:N> W conn.c123() as cur:N> T:N> cur.c124(<sql>, <params> or []) N> conn.c127() N< X c0 as e:N> conn.c128() N> c105.e(f"DBEXEC FAIL:{e}",exc_info=t) N> U N< < <` (Assumes db-api, c122=conn, c123=cursor, etc.)
* `DBFETCH1(<tgt>:<sql>[:<params>])` -> `W c122() as conn:N> W conn.c123() as cur:N> T:N> cur.c124(<sql>, <params> or []) N> <tgt> = cur.c125() N> conn.c127() N< X c0 as e:N> conn.c128() N> c105.e(f"DBFETCH1 FAIL:{e}",exc_info=t) N> U N< < <` (Assumes c125=fetchone)
* `CHKEXIT(<msg>:<exit_code>)` -> `_audit(<msg>) N _res = _report(...) N U c26(<exit_code>)` (Assumes funcs `_audit`, `_report`, c26=SystemExit)
* `CHKINIT(<var>:<Class>[:<args...>])` -> `G <var> N ? <var> ~ n : N > <var> = <Class>(*<args>) N <`
* `PATHJOIN(<tgt>:<part1>[:<parts...>])` -> `<tgt> = c115 . c78 (<part1>, *<parts>)` (Assumes c115=pathlib/os.path, c78=join)
* `MKDIRS(<path>)` -> `c115 . c121 (<path>, exist_ok=t)` (Assumes c115=os/pathlib, c121=makedirs)

---
**Encoding/Decoding Logic Summary:**
1.  **Decode:** Parse Header -> Get D/X/O -> Load C + Fixed Toks (from above) -> Tokenize Body -> Substitute c/d/l refs -> Expand SemToks -> Translate Fixed Toks -> Format (`N > <`). Verify C: hash.
2.  **Encode:** Parse Code -> Prioritize Semantic Token patterns -> Map Kw/Op to Fixed Toks -> Map IDs/Lits to C (`c<n>`) or build D (`d<n>`) -> Handle Lits (Inline vs X:`l<n>`) -> Handle comments (`cmt=k` -> X:`l<n>`) -> Insert Structure (`N > <`) -> Build Header -> Assemble `[Header]|||Body`.