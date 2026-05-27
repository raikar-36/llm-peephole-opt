define i64 @pattern_or_255_64(i64 %x) {
entry:
  %result = or i64 %x, 255
  ret i64 %result
}
