define i32 @pattern_or_255_32(i32 %x) {
entry:
  %result = or i32 %x, 255
  ret i32 %result
}
