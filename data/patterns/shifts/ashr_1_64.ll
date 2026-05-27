define i64 @pattern_ashr_1_64(i64 %x) {
entry:
  %result = ashr i64 %x, 1
  ret i64 %result
}
