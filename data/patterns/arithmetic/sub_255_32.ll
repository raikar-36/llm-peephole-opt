define i32 @pattern_sub_255_32(i32 %x) {
entry:
  %result = sub i32 %x, 255
  ret i32 %result
}
