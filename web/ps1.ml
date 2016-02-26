(* Solution for coded parts of PS1 *)
(* Note: no list folding yet *)

(* Solutions for all functions except every_nth and complete_list taken from
solution for FA2014 *)

(* every_nth *)
let every_nth (lst : 'a list) (n : int) : 'a list =
	let rec every_nth_helper (lst : 'a list) (acc : 'a list) (count : int) : 'a list =
		match lst with
		| [] -> acc
		| h::t -> let acc = if count = 1 then acc@[h] else acc in
			let count = if count = 1 then n else count-1 in
			every_nth_helper t acc count
	in
	every_nth_helper lst [] n


(* is_unimodal *)
let is_unimodal (lst : int list) =
	(*
	(*
	[descent lst] checks if the list is only descending
	 *)
	let descend lst = (List.sort compare lst) = (List.rev lst) in

	(* [increase lst p] releases the list at the point at which it stops increasing *)

	let rec increase lst p =
		match lst with |h::t -> if h >= p then increase t h else lst | [] -> lst in
	match lst with
	| h::t -> let d = increase lst h in descend d
	| [] -> true
  *)
	failwith "not implemented"

(* complete_list *)
let complete_list (lst : 'a list) : ('a list * 'a list) list =
	let rec complete_list_helper (front : 'a list) (back : 'a list)
		(acc : ('a list * 'a list) list) : ('a list * 'a list) list =
		match back with
		| [] -> acc
		| h::[] -> acc
		| h::t ->
			let front = front@[h] in
			let acc = (front,t)::acc in
			complete_list_helper front t acc
	in
	complete_list_helper [] lst []

let rev_int n =
	(*
	[rev_int_help] reverses [i] and then puts the digits into [acc]
	 *)
	let rec rev_int_help i acc =
		if i = 0 then acc
		else rev_int_help (i / 10) ((acc * 10) + (i mod 10))
	in
	if n < 0 then -(rev_int_help (abs n) 0)
	else rev_int_help n 0

(* unflatten *)
let unflatten i lst =
	if (i < 1) then None
	else begin

(* 		[subset] holds the elements of the list in the subset [sub]
			when the counter [cnt] reaches [i], [sub] is placed in the
			accumulator and the process repeats as we go through the list *)

		let rec subset lst acc sub cnt =
			match lst with
			| [] ->  List.rev (sub::acc)
			| h::t ->
				if cnt = i then subset t (sub::acc) [h] 1
				else subset t acc (sub @ [h]) (cnt + 1)
		in
		Some (subset lst [] [] 0)
	end

type numeral = I | V | X | L | C | D | M
type roman = numeral list

(* Might be able to make this more efficient *)
let rec int_of_roman (r : roman) : int =
	let int_of_numeral = function
		| I -> 1
		| V -> 5
		| X -> 10
		| L -> 50
		| C -> 100
		| D -> 500
		| M -> 1000
	in
	(*
		The second match case allows for the preceding value to
		be less than that of the current value [h2]
	*)
	match r with
	| [] -> 0
	| h::h2::t ->
		let h_int = int_of_numeral h in
		let h2_int = int_of_numeral h2 in
		if h_int < h2_int then (h2_int - h_int) + (int_of_roman t)
		else h_int + (int_of_roman (h2::t))
	| h::t ->
		(int_of_numeral h) + (int_of_roman t)
