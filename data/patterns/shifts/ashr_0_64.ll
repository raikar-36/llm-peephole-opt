define i64 @pattern_ashr_0_64(i64 %x) {
entry:
  %result = ashr i64 %x, 0
  ret i64 %result
}
