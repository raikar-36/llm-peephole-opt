define i64 @pattern_add_255_64(i64 %x) {
entry:
  %result = add i64 %x, 255
  ret i64 %result
}
