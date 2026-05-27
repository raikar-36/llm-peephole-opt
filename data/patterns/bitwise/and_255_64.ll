define i64 @pattern_and_255_64(i64 %x) {
entry:
  %result = and i64 %x, 255
  ret i64 %result
}
