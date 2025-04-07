# Python -> PLSP v0.5 Translation Mapping Spec v0.1 (MACHINE TARGET)

**GOAL:** Map Python script constructs to PLSP v0.5 execution model (Middleware `INSTR:` + LLM `S{...}S` state). Target: Simple scripts (vars, basic I/O, conditionals, loops). Non-target: Classes, complex functions, generators, advanced data structs (direct translation infeasible/inefficient), OS forks, threading, GUI, network servers (use Middleware signals `!` for simulation/external action).

**CORE PRINCIPLE:** Python execution flow -> Middleware control logic generating `INSTR:`. LLM only executes state updates based on `INSTR:`. State (`S{...}S`) MUST capture *all* Python runtime state needed (vars, loop counters, program counter equivalent like `$p` purpose).

**MAPPINGS:**

1.  **Variables (Scalar):**
    *   PY: `x = 10` | `s = "hi"` | `y = x`
    *   PLSP State (`S{...}S`): Use single-letter IDs. `$a:10` | `$b:"hi"` | `$c:$a`
    *   MW `INSTR:` (for init/update): `@set:$a=10;` | `@set:$b="hi";` | `@set:$c=$a;` (or `@upd:`)
    *   Mapping: Direct state representation. MW generates `@set`/`@upd` directives.

2.  **Print:**
    *   PY: `print("Val:", x)`
    *   MW `INSTR:` Logic: Generate directive to signal data logging.
    *   MW `INSTR:`: `@log:"Val:",$a;` (assuming x maps to $a)
    *   LLM `S{...}S` Effect: Includes `>"Val:",$a;`
    *   MW Post-Processing: Parses `>` data from `S{...}S` and logs/displays it.

3.  **Input:**
    *   PY: `name = input("Enter name: ")`
    *   Multi-Cycle PLSP:
        1.  MW `INSTR:`: `@prompt:"Enter name:",$n;` (Request input, store in future `$n`) -> LLM `S{...$p:"await_in";!prompt,"Enter name:",$n;}S`
        2.  MW: Executes `!prompt`, gets "UserX" from external source.
        3.  MW `INSTR:`: `@input_recv:"UserX",$n; @set:$n="UserX"; ...` (Signal input received, set var) -> LLM `S{...$n:"UserX";$p:"running";...}S`
    *   Mapping: Requires Middleware interaction for actual I/O via `!` signals. State `$p` tracks waiting state.

4.  **If/Elif/Else:**
    *   PY: `if x > 10: y = 5; z = 1 else: y = 0`
    *   MW `INSTR:` Logic: *Middleware* evaluates condition based on `$x` value in *current* `S{...}S`. Generates `INSTR:` containing *only* the directives for the executed branch.
    *   Cycle N (State `S{...$x:15...}S`): MW sees `$x`=15. Evaluates `15 > 10` (True).
    *   MW `INSTR:` Cycle N+1: `@comment:"if_true"; @set:$y=5; @set:$z=1; ...`
    *   Cycle M (State `S{...$x:5...}S`): MW sees `$x`=5. Evaluates `5 > 10` (False).
    *   MW `INSTR:` Cycle M+1: `@comment:"if_false"; @set:$y=0; ...`
    *   Mapping: Control flow logic resides *entirely* within Middleware `INSTR:` generation. LLM executes only the chosen path's assignments.

5.  **While Loop:**
    *   PY: `i = 0; while i < 3: print(i); i += 1`
    *   MW `INSTR:` Logic: Uses state var (`$p`, or loop flag) + counter (`$i`). MW checks condition each cycle based on `S{...}S`.
    *   Cycle 1 (Init): MW `INSTR:`: `@set:$i=0; @set:$p="loop_chk";` -> LLM `S{$i:0;$p:"loop_chk";}S`
    *   Cycle 2 (Check 0<3): MW reads `$i:0`. Cond TRUE. MW `INSTR:`: `@log:$i; @upd:$i=$i+1; @set:$p="loop_chk";` -> LLM `S{$i:1;$p:"loop_chk";>0;}S`
    *   Cycle 3 (Check 1<3): MW reads `$i:1`. Cond TRUE. MW `INSTR:`: `@log:$i; @upd:$i=$i+1; @set:$p="loop_chk";` -> LLM `S{$i:2;$p:"loop_chk";>1;}S`
    *   Cycle 4 (Check 2<3): MW reads `$i:2`. Cond TRUE. MW `INSTR:`: `@log:$i; @upd:$i=$i+1; @set:$p="loop_chk";` -> LLM `S{$i:3;$p:"loop_chk";>2;}S`
    *   Cycle 5 (Check 3<3): MW reads `$i:3`. Cond FALSE. MW `INSTR:`: `@set:$p="loop_end"; ...` -> LLM `S{$i:3;$p:"loop_end";...}S`
    *   Mapping: Loop control resides *entirely* within Middleware logic based on state checks. `$p` tracks position (in loop, ended).

6.  **For Loop (Simple Range):**
    *   PY: `for j in range(2): print(j)`
    *   Mapping: Translate to equivalent `while` loop (using counter, check). MW manages counter init, increment, check, and loop termination `INSTR:` directives.

7.  **Functions (Limited):**
    *   PY: `def my_func(a): return a + 1; y = my_func(5)`
    *   Mapping (Inlining): If simple, translator *inlines* code. `tmp = 5 + 1; y = tmp` -> `@tmp=5+1; @set:$y=$tmp;` (Assumes Middleware can handle simple expressions or trigger LLM calc tool).
    *   Mapping (Complex/Avoid): Direct translation of call stacks is highly complex and inefficient for PLSP. Avoid/Refactor Python code first. Middleware *could* simulate stack via state vars (`$ret_p`, `$arg_a`...) but is discouraged.

8.  **Imports:**
    *   PY: `import time; time.sleep(2)`
    *   MW `INSTR:`: `@sig:!wait,2000;`
    *   Mapping: Map stdlib functions to corresponding Middleware `!` actions (`wait`, `fetch`, `file_io` etc.) defined by the Middleware implementation. Translator needs mapping table `Python func -> !action`.

9.  **Data Structures (Limited):**
    *   PY: `my_list = [1, 2]` | `my_dict = {'a': 1}`
    *   Mapping (Simulated): Use indexed vars by convention. `$l0:1; $l1:2; $llen:2;` | `$da:1; $dkeys:"a";` Extremely clunky. Access/mutation requires complex Middleware logic in `INSTR:` (e.g., `@list_get:$l,1,$target;`). Avoid complex structures if possible.

**Translation Process Overview (for LLM Translator):**

1.  Receive Python script.
2.  Parse Python AST (Abstract Syntax Tree) or use code structure understanding.
3.  Initialize PLSP state representation (map Python vars to `$a`, `$b`...).
4.  Simulate Python execution step-by-step.
5.  For each step, determine the corresponding Middleware `INSTR:` directive(s) based on the Mapping Spec above.
6.  Determine the resulting `S{...}S` state block after the LLM would process that `INSTR:`.
7.  Handle control flow (if/while) by determining *which* `INSTR:` sequence the Middleware *would* generate based on the *current* simulated PLSP state.
8.  Output: Can be a sequence of (`INSTR:`, `Expected S{...}S`) pairs representing the translated execution flow, or potentially generate the Middleware logic itself (e.g., in Python) that implements the control flow and `INSTR:` generation.

**Limitations:** Direct, fully automated translation of arbitrary Python is likely impossible/impractical. Focus on simpler procedural scripts. Requires a capable Middleware component that understands the `INSTR:` directives and implements the `!` actions and control flow logic. Efficiency depends heavily on Middleware implementation and minimizing cycles/state size.