

let results = Pa_ounit_lib.Runtime.results ()

open Yojson.Basic

let unittest_name_of_line (line : string) : string =
  let pattern = Str.regexp "^File \".*\", line [0-9]+, characters [0-9]+-[0-9]+: \\(.*\\)$" in
  try
    let () = ignore (Str.search_forward pattern line 0) in
    Str.matched_group 1 line
  with _ -> line

let test_result_to_json (descr, result) =
  let json_result = match result with
  | Pa_ounit_lib.Runtime.Success -> [("passed", `Bool true); ("message", `Null)]
  | Pa_ounit_lib.Runtime.Failure message -> [("passed", `Bool false); ("message", `String message)] in
  `Assoc ([("name", `String (unittest_name_of_line descr))] @ json_result)

let json_results = `List (List.map test_result_to_json results)

let () = to_file "test-results.json" json_results
