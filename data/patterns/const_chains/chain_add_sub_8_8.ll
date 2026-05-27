define i32 @chain_add_sub_8_8(i32 %x) {
entry:
  %tmp = add i32 %x, 8
  %result = sub i32 %tmp, 8
  ret i32 %result
}
