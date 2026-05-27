define i64 @pattern_ashr_2_64(i64 %x) {
entry:
  %result = ashr i64 %x, 2
  ret i64 %result
}
