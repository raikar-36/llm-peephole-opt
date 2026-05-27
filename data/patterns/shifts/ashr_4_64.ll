define i64 @pattern_ashr_4_64(i64 %x) {
entry:
  %result = ashr i64 %x, 4
  ret i64 %result
}
