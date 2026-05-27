define i32 @pattern_add_255_32(i32 %x) {
entry:
  %result = add i32 %x, 255
  ret i32 %result
}
