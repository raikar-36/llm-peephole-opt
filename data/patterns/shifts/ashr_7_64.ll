define i64 @pattern_ashr_7_64(i64 %x) {
entry:
  %result = ashr i64 %x, 7
  ret i64 %result
}
