define i64 @pattern_ashr_3_64(i64 %x) {
entry:
  %result = ashr i64 %x, 3
  ret i64 %result
}
