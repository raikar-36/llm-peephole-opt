define i32 @pattern_sub_128_32(i32 %x) {
entry:
  %result = sub i32 %x, 128
  ret i32 %result
}
