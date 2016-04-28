let results = Pa_ounit_lib.Runtime.results ()

open Yojson.Basic

let test_result_to_json (descr, result) =
  let json_result = match result with
  | Pa_ounit_lib.Runtime.Success -> [("passed", `Bool true); ("message", `Null)]
  | Pa_ounit_lib.Runtime.Failure message -> [("passed", `Bool false); ("message", `String message)] in
  `Assoc ([("name", `String descr)] @ json_result)

let json_results = `List (List.map test_result_to_json results)

let () = to_file "test-results.json" json_results
