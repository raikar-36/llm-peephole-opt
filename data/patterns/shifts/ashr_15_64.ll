define i64 @pattern_ashr_15_64(i64 %x) {
entry:
  %result = ashr i64 %x, 15
  ret i64 %result
}
