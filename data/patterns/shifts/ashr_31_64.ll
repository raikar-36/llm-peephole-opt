define i64 @pattern_ashr_31_64(i64 %x) {
entry:
  %result = ashr i64 %x, 31
  ret i64 %result
}
